# -*- coding: utf-8 -*-
"""Translator portfolio book assistant. Uses public Google Books search, optional Kakao API.
All additions/changes require explicit user confirmation. No unattended publishing.
"""
import csv
import datetime
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import threading
import urllib.parse
import urllib.request

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'books.js'
COVERS=ROOT/'covers'
AGENT='Mozilla/5.0 (compatible; BookBibliographyUpdater/1.0)'


def parse_books():
    raw=DATA.read_text(encoding='utf-8')
    m=re.search(r'const\s+books\s*=\s*(\[.*?\])\s*;',raw,re.S)
    if not m: raise ValueError('books.js 에서 도서 목록을 찾지 못했습니다.')
    return raw,m,json.loads(m.group(1))


def norm(s):
    return re.sub(r'[^\w가-힣]', '', str(s or '')).casefold()


def request_json(url,headers=None):
    req=urllib.request.Request(url,headers={'User-Agent':AGENT,**(headers or {})})
    with urllib.request.urlopen(req,timeout=17) as r:
        if int(r.status)!=200:raise ValueError('HTTP '+str(r.status))
        return json.load(r)


def search_books(title, kakao_key=''):
    results=[]; errors=[]
    if kakao_key:
        try:
            url='https://dapi.kakao.com/v3/search/book?'+urllib.parse.urlencode({'query':title,'target':'title','size':20})
            data=request_json(url,{'Authorization':'KakaoAK '+kakao_key})
            for item in data.get('documents',[]):
                authors=item.get('authors',[])
                candidates=dict(title=re.sub(r'<[^>]+>','',item.get('title','')),author=', '.join(authors),publisher=item.get('publisher',''),year=str(item.get('datetime',''))[:4],url=item.get('url',''),cover=item.get('thumbnail',''),isbn=(item.get('isbn','').split() or [''])[0],source='카카오 도서')
                if candidates['title']:results.append(candidates)
        except Exception as e:errors.append('카카오 검색: '+str(e))
    try:
        url='https://www.googleapis.com/books/v1/volumes?'+urllib.parse.urlencode({'q':'intitle:'+title,'maxResults':40,'printType':'books'})
        data=request_json(url)
        for item in data.get('items',[]):
            v=item.get('volumeInfo',{})
            ids=v.get('industryIdentifiers') or []
            isbn=next((x['identifier'] for x in ids if x.get('type')=='ISBN_13'),next((x.get('identifier','') for x in ids),''))
            cover=(v.get('imageLinks') or {}).get('thumbnail','').replace('http://','https://')
            results.append(dict(title=v.get('title',''),author=', '.join(v.get('authors',[])),publisher=v.get('publisher',''),year=str(v.get('publishedDate',''))[:4],url=v.get('infoLink',''),cover=cover,isbn=isbn,source='Google 도서'))
    except Exception as e:errors.append('Google 검색: '+str(e))
    # Show candidates which closely match. Never assume a loose title match is the correct edition.
    key=norm(title)
    filtered=[b for b in results if norm(b['title']) and (key in norm(b['title']) or norm(b['title']) in key)]
    filtered.sort(key=lambda b:(norm(b['title'])!=key, b['source']!='카카오 도서',-len(b['publisher'])))
    unique=[];seen=set()
    for b in filtered:
        sig=(norm(b['title']),norm(b['author']),norm(b['publisher']),b['year'])
        if sig not in seen:unique.append(b);seen.add(sig)
    return unique[:25],errors


def img_extension(data,ctype=''):
    if data.startswith(b'\xff\xd8\xff'):return '.jpg'
    if data.startswith(b'\x89PNG\r\n\x1a\n'):return '.png'
    if data.startswith(b'RIFF') and data[8:12]==b'WEBP':return '.webp'
    if data.startswith((b'GIF87a',b'GIF89a')):return '.gif'
    return ''


def download_cover(url,book_id):
    if not url: return ''
    parsed=urllib.parse.urlparse(url)
    if parsed.scheme not in ('https','http'): raise ValueError('표지 URL은 http(s)이어야 합니다.')
    req=urllib.request.Request(url,headers={'User-Agent':AGENT,'Accept':'image/avif,image/webp,image/png,image/jpeg,image/*;q=0.8'})
    with urllib.request.urlopen(req,timeout=20) as resp:
        if int(resp.headers.get('Content-Length','0')) > 8*1024*1024: raise ValueError('표지 파일이 너무 큽니다.')
        data=resp.read(8*1024*1024+1);ctype=resp.headers.get('Content-Type','')
    if len(data)>8*1024*1024 or len(data)<1500:raise ValueError('표지 이미지 크기가 비정상적입니다.')
    ext=img_extension(data,ctype)
    if not ext:raise ValueError('이미지 파일이 아닙니다.')
    COVERS.mkdir(exist_ok=True)
    path=COVERS/f'{book_id:03}{ext}'
    # never overwrite existing file silently
    if path.exists():
        path=COVERS/f'{book_id:03}_updated_{datetime.datetime.now():%Y%m%d%H%M%S}{ext}'
    path.write_bytes(data)
    return 'covers/'+path.name


def save_book(book, original_title=None):
    raw,m,books=parse_books()
    match=None
    if original_title:
        match=next((x for x in books if norm(x.get('title'))==norm(original_title)),None)
    if not match:
        match=next((x for x in books if norm(x.get('title'))==norm(book['title'])),None)
    if match:
        target=match.copy(); target.update(book)
        target['id']=match['id']
        books[books.index(match)]=target
    else:
        target={'id':max((int(x['id']) for x in books),default=0)+1,**book}
        books.append(target)
    target['publication_status']='published'
    target['status']='서지 확인 필요'  # User confirmation is not third-party bibliographic validation
    target['verified']=False
    stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup=DATA.with_name('books_backup_'+stamp+'.js')
    backup.write_text(raw,encoding='utf-8')
    new=raw[:m.start(1)]+json.dumps(books,ensure_ascii=False,indent=2)+raw[m.end(1):]
    tmp=DATA.with_suffix('.js.tmp'); tmp.write_text(new,encoding='utf-8');os.replace(tmp,DATA)
    csvpath=ROOT/'bibliography.csv'
    cols=['id','title','author','publisher','year','url','cover','status','publication_status','isbn']
    with csvpath.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore');w.writeheader();w.writerows(books)
    return target['id'],bool(match),backup


def main():
    import tkinter as tk
    from tkinter import ttk,messagebox
    root=tk.Tk();root.title('이연승 번역서 등록 · 제목 검색');root.geometry('940x730');root.minsize(680,560)
    frame=ttk.Frame(root,padding=18);frame.pack(fill='both',expand=True)
    ttk.Label(frame,text='새 책 등록 / 출간 예정 도서 전환',font=('Malgun Gothic',16,'bold')).pack(anchor='w')
    ttk.Label(frame,text='제목만 입력해 검색 → 후보 선택 → 서지·표지 확인 → 저장. 자동 선택·자동 출간 처리는 하지 않습니다.',wraplength=850).pack(anchor='w',pady=(6,15))
    top=ttk.Frame(frame);top.pack(fill='x')
    ttk.Label(top,text='책 제목').pack(side='left');title_var=tk.StringVar();ent=ttk.Entry(top,textvariable=title_var);ent.pack(side='left',fill='x',expand=True,padx=10)
    entries={};found=[]
    search_btn=ttk.Button(top,text='온라인 검색');search_btn.pack(side='left')
    status=tk.StringVar(value='준비됨');ttk.Label(frame,textvariable=status,wraplength=850).pack(anchor='w',pady=8)
    ttk.Label(frame,text='검색 후보 (선택하면 아래 정보에 복사)').pack(anchor='w')
    listbox=tk.Listbox(frame,height=7,exportselection=False);listbox.pack(fill='x',pady=(4,12))
    info=ttk.LabelFrame(frame,text='등록할 정보 (수정 가능)',padding=12);info.pack(fill='x')
    for i,(key,label) in enumerate([('title','제목'),('author','저자'),('publisher','출판사'),('year','출간연도'),('url','도서 정보 링크'),('cover','표지 이미지 URL'),('isbn','ISBN')]):
        ttk.Label(info,text=label).grid(row=i,column=0,sticky='w',pady=3)
        v=tk.StringVar();e=ttk.Entry(info,textvariable=v,width=95);e.grid(row=i,column=1,sticky='ew',padx=10,pady=3);entries[key]=v
    info.columnconfigure(1,weight=1)
    note=ttk.Label(frame,text='검색이 안 되면 위 정보를 직접 입력할 수 있어. 표지 URL이 비어 있으면 표지를 자동으로 만들 수는 없어. 등록 전 출간연도·저자·판본을 반드시 확인해.',wraplength=850)
    note.pack(anchor='w',pady=(12,8))
    def choose(event=None):
        idx=listbox.curselection()
        if not idx:return
        b=found[idx[0]]
        for k,v in entries.items():v.set(str(b.get(k,'') or ''))
        status.set('후보 정보를 채웠습니다. 정확한 한국어 판본인지 확인한 후 저장하세요.')
    listbox.bind('<<ListboxSelect>>',choose)
    def search():
        title=title_var.get().strip()
        if not title:return messagebox.showwarning('제목 필요','책 제목을 입력해 주세요.')
        search_btn.config(state='disabled');status.set('온라인에서 찾는 중…')
        def work():
            keyfile=ROOT/'KAKAO_API_KEY.txt'
            key=keyfile.read_text('utf-8').strip() if keyfile.exists() else ''
            found_data,errors=search_books(title,key)
            def done():
                nonlocal found
                found=found_data;listbox.delete(0,'end')
                for b in found:listbox.insert('end',f"[{b['source']}] {b['title']} | {b['author']} | {b['publisher']} | {b['year']}")
                entries['title'].set(title)
                status.set(f'후보 {len(found)}건. '+ (' / '.join(errors) if errors else '후보를 선택하거나 직접 정보를 입력하세요.'))
                search_btn.config(state='normal')
            root.after(0,done)
        threading.Thread(target=work,daemon=True).start()
    search_btn.config(command=search)
    ent.bind('<Return>',lambda e:search())
    def save():
        b={k:v.get().strip() for k,v in entries.items()}
        if not b['title']:return messagebox.showwarning('확인','도서 제목이 필요합니다.')
        if b['year'] and (not re.fullmatch(r'\d{4}',b['year']) or not 1800<=int(b['year'])<=2100):return messagebox.showerror('출간연도','출간연도는 4자리 숫자로 입력해 주세요.')
        if not all((b['author'],b['publisher'],b['year'],b['url'])):
            if not messagebox.askyesno('정보 누락','저자·출판사·연도·정보 링크 중 빠진 항목이 있습니다. 그래도 등록할까요?'):return
        old=None
        _,_,current=parse_books()
        for x in current:
            if norm(x['title'])==norm(b['title']):old=x;break
        mode='기존 책을 업데이트' if old else '새 책을 추가'
        if not messagebox.askyesno('최종 확인',f"{mode}할까요?\n\n{b['title']}\n{b['author']} · {b['publisher']} · {b['year']}\n\n저장 후 출간 예정 표시는 해제됩니다."):return
        try:
            bookid=old['id'] if old else max(x['id'] for x in current)+1
            image_error=''
            if b['cover']:
                try:b['cover']=download_cover(b['cover'],bookid)
                except Exception as e:
                    image_error=str(e)
                    b['cover']=old.get('cover','') if old else ''
            else:b['cover']=old.get('cover','') if old else ''
            b['year']=int(b['year']) if b['year'] else None
            b['original_title']=old.get('original_title',b['title']) if old else b['title']
            b['cover_status']='사용자 등록/확인 필요' if b['cover'] else '표지 미확보'
            resultid,updated,backup=save_book(b)
            messagebox.showinfo('저장 완료',f"#{resultid:03d} {'업데이트' if updated else '신규 등록'} 완료.\nbooks.js 저장 및 백업 완료.\nindex.html을 새로 열거나 Ctrl+F5로 새로고침하세요." + ('\n\n표지 다운로드 실패: '+image_error if image_error else ''))
            status.set('저장 완료. 도서 정보는 books.js에 반영됐습니다.')
        except Exception as e:messagebox.showerror('저장 실패',str(e))
    ttk.Button(frame,text='확인한 정보로 홈페이지에 저장',command=save).pack(anchor='e',pady=(6,0))
    root.mainloop()


if __name__=='__main__':
    if '--self-test' in sys.argv:
        assert norm('살육의 광시곡')==norm('살육 의 광시곡')
        raw,m,books=parse_books();assert len(books)==96
        assert len([x for x in books if x.get('publication_status')=='upcoming'])==3
        assert len([x for x in books if x['title']=='뱀파이어 프린세스' and x['year']==2013])==1
        print('Self-test passed')
    else:main()
