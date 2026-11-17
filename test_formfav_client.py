import io,json,tempfile,unittest
from urllib.error import HTTPError
from formfav_client import Client,FormFavError,capture

class FormFavClientTests(unittest.TestCase):
    def test_auth_header_not_query(self):
        requests=[]
        def opened(req,timeout):
            requests.append(req)
            return io.BytesIO(b'{"tier":"pro"}')
        c=Client('test-only-secret',opened)
        self.assertEqual(c.get('/usage')['tier'],'pro')
        self.assertEqual(requests[0].get_header('X-api-key'),'test-only-secret')
        self.assertNotIn('secret',requests[0].full_url)

    def test_http_error_body_cannot_leak_key(self):
        count=[]
        def opened(req,timeout):
            count.append(1)
            raise HTTPError(req.full_url,429,'secret',{},io.BytesIO(b'test-only-secret'))
        with self.assertRaises(FormFavError) as ctx:Client('test-only-secret',opened).get('/usage')
        self.assertNotIn('secret',str(ctx.exception))
        self.assertEqual(len(count),1)

    def test_predictions_endpoint_not_allowed(self):
        with self.assertRaises(FormFavError):Client('test-only').get('/predictions')

    def test_statistics_name_is_encoded_as_one_path_segment(self):
        requests=[]
        def opened(req,timeout):
            requests.append(req)
            return io.BytesIO(b'{}')
        Client('test-only',opened).stats('trainer','One / Two',90)
        self.assertIn('One%20%2F%20Two',requests[0].full_url)

    def test_stats_invalid_window_rejected_before_network(self):
        with self.assertRaises(FormFavError):Client('test-only').stats('jockey','Damian Lane',366)

    def test_capture_rejects_wrong_race_date(self):
        class Fake:
            def get(self,path,params=None):
                if path=='/usage':return {'tier':'pro'}
                if path=='/form/meetings':return {'meetings':[{'track':'Belmont','slug':'belmont','country':'au','races':[{'raceNumber':1}]}]}
                return {'date':'2026-11-17','raceNumber':1,'runners':[]}
        with tempfile.TemporaryDirectory() as out:
            with self.assertRaises(FormFavError):capture('2026-11-18',out,client=Fake())

if __name__=='__main__':unittest.main()
