import re, json, hashlib

SL = open('/workspace/casebuild/bcg-starlight-cinemas-case/index.html').read()
BODY = open('body.html').read()

# --- head shell: everything before the rail nav ---
cut = SL.index('<nav class="rail"')
head = SL[:cut]
head = head.replace('<title>Starlight Cinemas Mock Case</title>', '<title>Unicloth Mock Case</title>')

rail = '''<nav class="rail" aria-label="Case steps">
  <div class="rail-in">
    <a class="home-pill" href="/">All cases</a>
    <div class="chips" id="chips">
      <a href="#primer">Primer</a><a href="#prompt">Prompt</a><a href="#clarify">Clarify</a><a href="#framework">Framework</a><a href="#revenue">Revenue</a><a href="#costs">Costs</a><a href="#ideas">Ideas</a><a href="#fix">Fix</a><a href="#recommend">Recommend</a><a href="#drills">Drills</a><a href="#test">Test</a>
    </div>
    <label class="speed" for="rate"><span>Speed</span>
      <select id="rate" aria-label="Read-aloud speed">
        <option value="0.9">0.9×</option><option value="1" selected>1×</option><option value="1.15">1.15×</option><option value="1.3">1.3×</option>
      </select>
    </label>
  </div>
</nav>
'''

# --- JS machinery from starlight ---
js_start = SL.index('<script>\n(function(){')
js_end = SL.index('<script src="tts.js">')
js = SL[js_start:js_end]

DATA = '''  const PAGEKEY="unicloth";
  /* Exhibit 1: cost stack */
  hbar($("#costchart"),[
    {d:"COGS",t:"70% of revenue, rounded",v:90,lab:"$90M",tip:"COGS: $90M a year"},
    {d:"Rent",t:"$18M flagship + $7.2M mall stores",v:25,lab:"$25M",tip:"Rent: $25M a year"},
    {d:"Storage, returns, markdowns",t:"Handling unsold inventory",v:12,lab:"$12M",tip:"Storage, returns, markdowns: $12M a year"},
    {d:"Labor",t:"560 associates and 9 managers",v:6,lab:"$6M",tip:"Labor: $6M a year"},
    {d:"Maintenance and utilities",t:"Upkeep of four stores",v:5,lab:"$5M",tip:"Maintenance and utilities: $5M a year"},
  ],{max:150,ticks:[0,50,100,150],tick:v=>"$"+v+"M",ref:{at:125,note:"The vertical line is revenue: $125M a year. Costs add to $138M, so Unicloth is $13M in the red."}});
  /* Exhibit 3: the three levers */
  hbar($("#fixchart"),[
    {d:"Ship by sea instead of air",t:"5% of the $90M COGS base",v:4.5,lab:"$4.5M",tip:"Sea shipping: +$4.5M a year"},
    {d:"Coffee partner in the flagship",t:"Shared rent on Fifth Avenue",v:1.75,lab:"$1.75M",tip:"Coffee partner: +$1.75M a year"},
    {d:"US redesign, net",t:"+$23M revenue − $12M cost",v:11,lab:"$11M",tip:"US redesign: +$11M a year, net"},
  ],{max:15,ticks:[0,5,10,15],tick:v=>"$"+v+"M",ref:{at:13,note:"The vertical line is the $13M gap. The three levers together clear it with about $4.25M to spare."}});
  /* Ideas scorer */
  heatScorer({xName:"Ease",yName:"Impact",xs:"E",ys:"I",lx:["Hard","","Medium","","Easy"],ly:["Small","","Medium","","Big"],items:[
    {id:"A",n:"Ship clothing by sea instead of air",x:5,y:3,w:"Cheap to do, and the clothes are not urgent: about 5% of COGS, roughly $4.5M a year."},
    {id:"B",n:"Bring a coffee shop into the flagship",x:4,y:3,w:"A partner shares the rent and pulls in more foot traffic. Worth $1.75M a year in the case."},
    {id:"C",n:"Redesign the US line: styles, colors, sizes",x:2,y:5,w:"Costs $12M a year but management estimates $23M of extra revenue. The only idea that fixes the root cause."},
    {id:"D",n:"Close the three mall stores",x:1,y:1,w:"Management is not ready: they want to expand into the suburbs later."},
    {id:"E",n:"Move the flagship off Fifth Avenue",x:1,y:1,w:"No: the flagship is the marketing."},
    {id:"F",n:"Launch an online store",x:3,y:2,w:"A real option eventually, but management says they are not ready for the investment."},
  ]});

  '''

TEST = '''  const TEST=[
    {q:"In a candidate-led case, who decides what to analyze next?",o:["You do","The interviewer, always","The client","Nobody; it is random"],a:0,w:"You set the structure, choose where to dig, and ask for data. The interviewer follows and pushes back."},
    {q:"Unicloth's revenue is $125M and its costs are $138M. The result is…",o:["$13M of profit","$13M in the red","$263M of revenue","Exactly break-even"],a:1,w:"Costs exceed revenue by 13 million. That gap is what the three levers have to close."},
    {q:"The margin on clothing is 30%. COGS on $125M of revenue is…",o:["$37.5M","$95M","$87.5M","$125M"],a:2,w:"If Unicloth keeps 30%, the clothes cost 70%: 125 times 0.7 is 87.5 million, rounded to 90 in the case."},
    {q:"Which of Unicloth's costs is fixed?",o:["Flagship rent","COGS","Sea freight per item","Markdowns"],a:0,w:"Rent stays the same whether the store sells 100 items or 10,000. The others move with sales."},
    {q:"The flagship sells 4,500 items a day at $40. Daily revenue is…",o:["$18K","$45K","$180K","$1.8M"],a:2,w:"4,500 times 40 is 180 thousand a day, about 66 million a year. One store outsells all three mall stores combined."},
    {q:"Why doesn't Unicloth just lower prices?",o:["Prices are set by suppliers","It would deepen the loss: this is a margin problem","Competitors would match instantly","Lower prices raise COGS"],a:1,w:"Unicloth loses money because costs exceed revenue. Cutting price cuts revenue per item and makes the gap worse. The casebook's interviewer says no to this idea."},
    {q:"Switching from air to sea saves 5% of a $90M COGS base. Annual savings:",o:["$4.5M","$45M","$450K","$9M"],a:0,w:"90 million times 5% is 4.5 million a year."},
    {q:"The US redesign costs $12M a year and adds $23M of revenue. Net effect:",o:["+$23M","−$12M","+$11M","+$35M"],a:2,w:"23 minus 12 is 11 million net. It costs money and makes money; the net is what counts."},
    {q:"Why keep the flagship despite $18M of annual rent?",o:["Leases cannot be broken","It is the marketing: the brand's showcase","Mall stores cost more per store","The flagship barely loses money"],a:1,w:"The casebook is explicit: moving the flagship is off the table because it carries the brand. A store can be judged on image, not just profit."},
    {q:"Styles too conservative, colors too muted, sizes run small. This is a problem of…",o:["Distribution","Pricing","Labor","Product-market fit"],a:3,w:"The product itself does not fit US customers. That is why the redesign is the biggest lever."},
    {q:"Which is the strongest opening line for the recommendation?",o:["Let me walk you through everything I looked at.","Retail is a tough business right now.","It depends on what the CEO wants.","Unicloth can turn profitable this year with three moves: sea shipping, a flagship rent partner, and a US redesign."],a:3,w:"Lead with the answer, then support it. Consultants call this answer-first, or the pyramid principle."},
    {q:"Costs are $138M, revenue $125M, and the levers add $17.25M. Profit after all three is…",o:["$4.25M","$17.25M","$13M","$30.25M"],a:0,w:"17.25 minus the 13 million gap leaves about 4.25 million. Candidates who say 17.25 forgot the hole they were filling."},
  ];
  '''

i = js.index('const PAGEKEY=')
j = js.index('const TEST=[')
k = js.index('  const testq=')
js = js[:i] + DATA + 'const TEST=[' + TEST[js.index('const TEST=[')+len('const TEST=['):] if False else js
# simpler: rebuild
js_new = js[:i] + DATA.lstrip() + 'const TEST=[' + TEST[js.index('const TEST=[')+len('const TEST=['):].lstrip('\n') + js[k:]
page = head + rail + BODY + '\n' + js_new
open('index.html','w').write(page)
print('index.html bytes:', len(page))
print('PAGEKEY ok:', 'unicloth' in page, '| starlight refs:', page.count('Starlight'))
