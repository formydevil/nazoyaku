// 도서 데이터: books.js. 확인 상태는 서지와 표지 URL 상태를 엄격히 구분합니다.
const grid=document.querySelector('#bookGrid');
const search=document.querySelector('#search');
const more=document.querySelector('#more');
const empty=document.querySelector('#noResults');
const filter=document.querySelector('#statusFilter');
const sortBy=document.querySelector('#sortBy');
const resultCount=document.querySelector('#resultCount');
const PAGE_SIZE=15; // Desktop: five books per row, three complete rows
let limit=PAGE_SIZE;
const isUpcoming=b=>b.publication_status==='upcoming'||b.status==='미출간';
const upcomingOrder=['작은 이방인','멋진 압박','살육의 광시곡'];
const upcomingRank=b=>{const n=upcomingOrder.indexOf(b.title);return n<0?99:n};
const summary=document.querySelector('#archiveSummary');
if(summary){const upcoming=books.filter(isUpcoming).length;summary.textContent=`총 ${books.length}권 · 출간 ${books.length-upcoming}권 · 출간 예정 ${upcoming}권 · 출간 예정 우선 / 출간연도 최신순`;}

const validText=(x)=>String(x??'').toLocaleLowerCase('ko');
function filteredBooks(){
  const q=validText(search.value.trim());
  const list=books.filter(b=>{
    const found=[b.title,b.original_title,b.author,b.publisher,b.year,b.isbn].map(validText).join(' ').includes(q);
    const ok=filter.value==='all' || (filter.value==='verified'&&b.verified) ||
      (filter.value==='covers'&&!!b.cover) || (filter.value==='pending'&&!b.verified);
    return found&&ok;
  });
  if(sortBy.value==='newest') list.sort((a,b)=>(Number(isUpcoming(b))-Number(isUpcoming(a))) || (isUpcoming(a)&&isUpcoming(b)?upcomingRank(a)-upcomingRank(b):0) || ((b.year||0)-(a.year||0)) || b.id-a.id);
  if(sortBy.value==='oldest') list.sort((a,b)=>(Number(isUpcoming(b))-Number(isUpcoming(a))) || (isUpcoming(a)&&isUpcoming(b)?upcomingRank(a)-upcomingRank(b):0) || ((a.year||9999)-(b.year||9999)) || a.id-b.id);
  return list;
}
function render(){
  const results=filteredBooks(); grid.replaceChildren();
  resultCount.textContent=`${results.length}개 항목 · ${Math.min(limit,results.length)}개 표시`;
  for(const b of results.slice(0,limit)){
    const card=document.createElement('article'); card.className='book-card';
    const cover=document.createElement('div');cover.className='book-cover';
    const placeholder=document.createElement('div');placeholder.className='cover-placeholder';placeholder.textContent=b.title;
    cover.append(placeholder);
    if(b.cover){
      const img=document.createElement('img');img.src=b.cover;img.alt=`${b.title} 서점 제공 표지`;
      img.loading='eager';img.referrerPolicy='no-referrer';
      img.addEventListener('load',()=>{if(img.naturalWidth>40){cover.classList.add('has-image');}});
      img.addEventListener('error',()=>{cover.classList.remove('has-image');img.remove();});
      cover.append(img);
    }
    const info=document.createElement('div'); info.className='book-info';
    const h=document.createElement('h3');h.textContent=b.title+(isUpcoming(b)?' (출간 예정)':'');
    const p=document.createElement('p');p.textContent=[b.author||'저자 확인 필요',b.publisher||'출판사 확인 필요',isUpcoming(b)?'출간 예정':(b.year||'출간연도 확인 필요')].join(' · ');
    info.append(h,p);
    
    if(b.url){const a=document.createElement('a');a.href=b.url;a.target='_blank';a.rel='noopener noreferrer';a.textContent='출처 · 도서 정보 ↗';info.append(a)}else if(!isUpcoming(b)){const note=document.createElement('p');note.className='missing-link';note.textContent='도서 상세 페이지 확인 필요';info.append(note)}
    card.append(cover,info); grid.append(card);
  }
  empty.hidden=results.length>0; more.hidden=results.length<=limit; more.disabled=results.length<=limit;
}
function reset(){limit=PAGE_SIZE;render()}
for(const el of [search,filter,sortBy]) el.addEventListener(el===search?'input':'change',reset);
more.addEventListener('click',()=>{limit+=PAGE_SIZE;render()});render();
const featuredTitles=[
  '폭탄',
  '영겁관 초연속 살인 사건',
  '용신 연못의 작은 시체',
  '어리석은 자의 독',
  '살인의 쌍곡선',
  '그 가능성은 이미 떠올렸다',
  '체육관의 살인',
  '히포크라테스 우울'
];
const slideColors=['#e7e5de','#e9e8e2','#e6e6df','#e5e4df','#e6e8e4','#e8e3df','#e4e5e3','#e7e5df'];
const slides=featuredTitles.map((title,i)=>({title,bg:slideColors[i]}));
let slide=0,playing=true;
const art=document.querySelector('#slideArt');
const caption=document.querySelector('#slideCaption');
const count=document.querySelector('#slideCount');
const slideCover=document.querySelector('#slideCover');
const mark=document.querySelector('#slideMark');
const toggle=document.querySelector('#toggle');
function show(){
  const s=slides[slide]; const b=books.find(x=>x.title===s.title);
  art.style.background=s.bg;caption.textContent=b ? [b.title,b.author].filter(Boolean).join(" · ") : s.title;
  mark.hidden=true;
  slideCover.style.display='block'; slideCover.src=(b && b.cover) || ''; slideCover.alt=s.title+' 표지';
  slideCover.onerror=()=>{slideCover.style.display='none';mark.hidden=false};
  count.textContent=String(slide+1).padStart(2,'0')+' / '+String(slides.length).padStart(2,'0');
}
document.querySelector('#prev').addEventListener('click',()=>{slide=(slide+slides.length-1)%slides.length;show()});
document.querySelector('#next').addEventListener('click',()=>{slide=(slide+1)%slides.length;show()});
toggle.addEventListener('click',()=>{playing=!playing;toggle.textContent=playing?'자동 넘김 정지':'자동 넘김 시작'});
setInterval(()=>{if(playing&&!document.hidden){slide=(slide+1)%slides.length;show()}},5000);show();
