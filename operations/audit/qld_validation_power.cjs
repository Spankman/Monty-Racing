// Offline design sensitivity for the Queensland 2027 Q1 prospectively locked cohort.
// Run: node operations/audit/qld_validation_power.cjs. No data access or fitting.
function plan() {
  const alpha = .05;
  const zTwoSided = 1.95996398454;
  const z80 = .841621233573;
  const z = zTwoSided + z80;
  const round = (x, places=6) => Number(x.toFixed(places));
  const ceiling = (n) => Math.ceil(n);
  function cdf(x) {
    const ax = Math.abs(x);
    const t = 1/(1+.2316419*ax);
    const q = Math.exp(-ax*ax/2)/Math.sqrt(2*Math.PI)*
      t*(.31938153+t*(-.356563782+t*(1.781477937+t*(-1.821255978+t*1.330274429))));
    return x >= 0 ? 1-q : q;
  }
  function normalPower(effect, se) {
    return cdf(effect/se-zTwoSided)+cdf(-effect/se-zTwoSided);
  }
  function binomial(n,p) {
    const mode = Math.floor((n+1)*p);
    const a = Array(n+1).fill(0);
    a[mode] = 1;
    for(let k=mode;k>0;k--) a[k-1]=a[k]*k/(n-k+1)*(1-p)/p;
    for(let k=mode;k<n;k++) a[k+1]=a[k]*(n-k)/(k+1)*p/(1-p);
    const mass = a.reduce((x,y)=>x+y,0);
    return a.map(x=>x/mass);
  }
  function exactUpperPower(n, p0, p1) {
    const h0 = binomial(n,p0);
    const h1 = binomial(n,p1);
    let falsePositive=0, power=0, criticalWins=n+1;
    for (let k=n; k>=0; k--) {
      if (falsePositive+h0[k]>alpha/2) break;
      falsePositive+=h0[k];
      power+=h1[k];
      criticalWins=k;
    }
    return {criticalWins, size:round(falsePositive), power:round(power)};
  }
  function roiRequired(price, effect, design) {
    const p0=1/price,p1=(1+effect)/price;
    const sd0=price*Math.sqrt(p0*(1-p0)), sd1=price*Math.sqrt(p1*(1-p1));
    return ceiling(design*((zTwoSided*sd0+z80*sd1)/effect)**2);
  }
  const history = {races:4129, ci:[-.0011961148107358668,.0017920466431703738],
                   roughieSelections:[348,617,448,2442]};
  // The archive interval already reflects day clustering. No further design-effect
  // multiplier is applied to the score anchor in this approximation.
  const scoreSpread=(history.ci[1]-history.ci[0])/(2*zTwoSided)*Math.sqrt(history.races);
  const census=1440;
  const admissions=[.25,.50,.75,1].map(x=>Math.round(census*x));
  const targetLogLoss=[.001,.002,.005];
  const design=1.4;
  const scoreScenarios=admissions.map(n=>({
    races:n, mdeLogLoss:round(z*scoreSpread/Math.sqrt(n)),
    stressedMdeLogLoss:round(z*.075/Math.sqrt(n)),
    logLossPowers:targetLogLoss.map(e=>round(normalPower(e,scoreSpread/Math.sqrt(n)))),
    mdeBrier:[.05,.10].map(sd=>round(z*sd/Math.sqrt(n))),
    mdePairedWinRoi:[.5,1,2].map(sd=>round(z*sd*Math.sqrt(design/n))),
    mdeWinStrike:[.05,.10,.20].map(q=>round(z*Math.sqrt(design*q/n))),
    calibrationMdeAtOneObservationPerRace:round(z*Math.sqrt(design*.1*.9/n)),
  }));
  const roi = [3,15,30,50,80].map((price,i)=>{
    const rate=i===0 ? 1 : history.roughieSelections[i-1]/history.races;
    const n=Math.round(720*rate);
    return {
      price, selectionRateProxy:round(rate), selectionsAt720:n,
      expectedWinsAtBreakEven:round(n/price,2),
      independentExactPowerAtPlus10pct:exactUpperPower(n,1/price,1.1/price),
      approximateSelectionsForNetROI5pct:roiRequired(price,.05,design),
      approximateSelectionsForNetROI10pct:roiRequired(price,.10,design),
    };
  });
  if (Math.abs(cdf(0)-.5)>1e-6 || exactUpperPower(2,.5,.6).power!==0 ||
      exactUpperPower(100,.3,.3).power>.025 ||
      scoreScenarios[0].mdeLogLoss<=scoreScenarios[1].mdeLogLoss ||
      roi[4].approximateSelectionsForNetROI10pct<=roi[3].approximateSelectionsForNetROI10pct) {
    throw new Error("Power calculation checks failed");
  }
  return {
    history, assumedCensus:census, maximumDays:84, designEffectForOtherEndpoints:design,
    historicalEffectiveLogLossSpread:round(scoreSpread),
    logLossTargets:targetLogLoss,
    logLossRequiredRaces:targetLogLoss.map(effect=>ceiling((z*scoreSpread/effect)**2)),
    logLossRequiredRacesStressed:targetLogLoss.map(effect=>ceiling((z*.075/effect)**2)),
    scoreScenarios, roi,
    calibrationExamplesAt80pct:[.01,.02,.03].map(gap=>({gap,
      binObservations:ceiling(design*(z*Math.sqrt(.1*.9)/gap)**2)})),
    strikeRacesAt10pctDiscordance:[.01,.02,.03].map(gap=>({gap,
      races:ceiling(design*.10*(z/gap)**2)})),
  };
}
if (typeof module !== "undefined" && require.main === module) {
  console.log(JSON.stringify(plan(), null, 2));
}
