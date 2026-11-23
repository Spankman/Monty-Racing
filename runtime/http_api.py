"""Authenticated REST and stateless MCP adapter; TLS must terminate at the host/gateway."""
import argparse
import hashlib
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import time

from runtime.service import Service,FrozenEngine,canonical
from runtime.provider import Provider


class API(ThreadingHTTPServer):
    daemon_threads=True
    def __init__(self,address,service,execute_token,read_token=None):
        if len(execute_token)<32 or read_token is not None and len(read_token)<32:
            raise ValueError('Configure strong runtime authentication tokens securely')
        if read_token==execute_token:raise ValueError('Read and execution credentials must differ')
        super().__init__(address,Handler);self.service=service
        self.tokens={hashlib.sha256(execute_token.encode()).digest():'execute'}
        if read_token:self.tokens[hashlib.sha256(read_token.encode()).digest()]='read'


class Handler(BaseHTTPRequestHandler):
    server_version='Monty/1'
    def setup(self):
        super().setup();self.connection.settimeout(15)
    def log_message(self,*args):pass  # No headers, credentials, provider errors or body logs.
    def role(self):
        header=self.headers.get('Authorization','')
        if not header.startswith('Bearer '):return None
        digest=hashlib.sha256(header[7:].encode()).digest()
        for expected,role in self.server.tokens.items():
            if hmac.compare_digest(digest,expected):return role
        return None
    def send(self,status,data):
        raw=json.dumps(data,ensure_ascii=False,allow_nan=False).encode()
        self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
    def do_GET(self):
        if not self.role():return self.send(401,{'error':'AUTHENTICATION_REQUIRED'})
        if self.path=='/health':return self.send(200,{'status':'runtime_alive','runtime':'frozen-python','inference_readiness':'UNVERIFIED','deployment_acceptance':'UNVERIFIED'})
        m=re.fullmatch('/v1/status/([a-f0-9]{32})',self.path)
        if not m:return self.send(404,{'error':'NOT_FOUND'})
        d=self.server.service.status(m[1]);return self.send(404 if d['request_status']=='NOT_FOUND' else 200,d)
    def do_POST(self):
        role=self.role()
        if not role:return self.send(401,{'error':'AUTHENTICATION_REQUIRED'})
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=16384:return self.send(413,{'error':'BODY_LIMIT'})
            body=json.loads(self.rfile.read(length))
            if not isinstance(body,dict):raise ValueError()
            if self.path=='/mcp':return self.mcp(body,role)
            if self.path!='/v1/commands':return self.send(404,{'error':'NOT_FOUND'})
            return self.send(200,self.call(body,role))
        except PermissionError:return self.send(403,{'error':'READ_ONLY_TOKEN'})
        except (ValueError,KeyError,TypeError):return self.send(400,{'error':'INVALID_COMMAND_PARAMETERS'})
        except Exception:return self.send(500,{'error':'SERVICE_FAILURE'})
    def call(self,body,role):
        if set(body)-{'command','date','country','request_id','wait_seconds'}:raise ValueError()
        text=body['command'];wait=body.get('wait_seconds',0)
        if not isinstance(text,str) or type(wait) not in (int,float) or not 0<=wait<=10:raise ValueError()
        if role!='execute' and text.strip().upper()!='C':raise PermissionError()
        if body.get('request_id') is not None and not re.fullmatch('[a-f0-9]{32}',str(body['request_id'])):raise ValueError()
        idem=self.headers.get('Idempotency-Key')
        if idem is not None and (not 1<=len(idem)<=128 or '\n' in idem):raise ValueError()
        d=self.server.service.submit(text,date=body.get('date'),country=body.get('country'),request_id=body.get('request_id'),idempotency_key=idem)
        end=time.monotonic()+wait
        while d['request_status'] in ('QUEUED','RUNNING') and time.monotonic()<end:
            time.sleep(.05);d=self.server.service.status(d['request_id'])
        return d
    def mcp(self,b,role):
        method=b.get('method');ident=b.get('id');params=b.get('params') or {}
        result=None
        if method=='server/discover':result={'supportedVersions':['2026-07-28'],'capabilities':{'tools':{}}}
        elif method=='initialize':result={'protocolVersion':'2025-03-26','capabilities':{'tools':{}},'serverInfo':{'name':'monty-frozen-runtime','version':'1.0.0'}}
        elif method=='notifications/initialized':return self.send(200,{})
        elif method=='tools/list':
            result={'tools':[{'name':'monty_execute','description':'Execute RM6, RM7, provisional PS aliases or a single race using both frozen engines and one provider capture. No wagers. Returns cache immediately or a request ID. Never use for C.',
                'inputSchema':{'type':'object','properties':{'command':{'type':'string'},'date':{'type':'string'},'country':{'type':'string','enum':['AU','NZ']},'wait_seconds':{'type':'number','minimum':0,'maximum':10}},'required':['command'],'additionalProperties':False},
                'annotations':{'readOnlyHint':False,'destructiveHint':False,'idempotentHint':False,'openWorldHint':True}},
                {'name':'monty_status','description':'C: read-only request status, capture age, expiry, immutable receipt and fresh ticket. Never queues inference or refreshes provider data.',
                 'inputSchema':{'type':'object','properties':{'request_id':{'type':'string'}},'additionalProperties':False},
                 'annotations':{'readOnlyHint':True,'destructiveHint':False,'idempotentHint':True,'openWorldHint':False}}]}
        elif method=='tools/call':
            try:
                name=params['name'];args=dict(params.get('arguments') or {})
                if name=='monty_status':
                    if set(args)-{'request_id'}:raise ValueError()
                    value=self.server.service.status(args.get('request_id'))
                elif name=='monty_execute':value=self.call(args,role)
                else:raise ValueError()
                result={'content':[{'type':'text','text':json.dumps(value,ensure_ascii=False)}],'structuredContent':value,'isError':False}
            except PermissionError:result={'content':[{'type':'text','text':'READ_ONLY_TOKEN'}],'isError':True}
            except (ValueError,TypeError,KeyError):result={'content':[{'type':'text','text':'INVALID_COMMAND_PARAMETERS'}],'isError':True}
        else:return self.send(200,{'jsonrpc':'2.0','id':ident,'error':{'code':-32601,'message':'Method not found'}})
        return self.send(200,{'jsonrpc':'2.0','id':ident,'result':result})


def main():
    p=argparse.ArgumentParser();p.add_argument('--bind',default='127.0.0.1');p.add_argument('--port',default=8080,type=int)
    p.add_argument('--data',type=Path,required=True);p.add_argument('--v7-root',type=Path,required=True);a=p.parse_args()
    # No token defaults, secret generation or external credential lookup.
    service=Service(a.data,Provider(os.environ.get('KROK_API_KEY',''),budget=20),FrozenEngine(a.v7_root))
    try:
        server=API((a.bind,a.port),service,os.environ.get('MONTY_EXECUTE_TOKEN',''),os.environ.get('MONTY_READ_TOKEN'))
        server.serve_forever()
    finally:service.close()

if __name__=='__main__':main()
