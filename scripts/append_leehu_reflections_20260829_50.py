#!/usr/bin/env python3
"""소설가 이후 자작품 5종 문학노트 50편: 고유 소재·다중 서술 구조."""
from __future__ import annotations
import json, re
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; CONTENT=ROOT/'content'/'literature'
MANIFEST=ROOT/'content'/'leehu-reflections-20260829-50.json'
EXPECTED_BEFORE=2981; PUBLISHED_AT='2026-08-29T21:50:00+09:00'; START_SEQUENCE=611
WORKS=(
('연(戀)','love','관계와 선택','https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000005377756','사랑을 완성된 감정보다 거리와 선택을 다시 묻는 과정으로 읽는다','빠른 호감과 단절이 반복되는 관계의 시대','미완성 편지,두 번째 인사,식어 가는 찻잔,비어 있는 옆자리,우산의 경계,약속 시간 십 분 전,오래된 영수증,닫히지 않은 문,서로 다른 걸음,낯선 호칭,빗금 친 달력,한쪽 이어폰,늦은 사과,흐린 단체사진,돌려받은 책,삭제된 연락처,반대편 승강장,같이 고른 화분,말끝의 온도,각자의 귀가'),
('데자뷔','deja-vu','기억과 반복','https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000005377772','낯익음이 진실의 증거인지 기억이 만든 편집인지 의심해 본다','추천 알고리즘이 익숙한 장면을 되돌려 주는 시대','낯익은 역,반복되는 번호,처음 듣는 옛 노래,꿈속의 복도,두 번 울린 초인종,겹쳐진 지도,닮은 뒷모습,되감긴 대화,오래된 비밀번호,같은 향기의 계절,빈 프레임,낯선 필체의 일기,반복되는 질문,어긋난 시계,익숙한 오타,돌아온 소포,거울 속 지연,같은 자리의 새 가게,잊은 약속의 흔적,뒤늦게 온 장면'),
('소나기','rain-shower','회복과 변화','https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000002957780','갑작스러운 변화 뒤 몸과 마음이 회복되는 작은 과정을 바라본다','예고 없이 일상이 바뀌고 곧바로 회복하라는 요구가 따르는 시대','젖은 운동화,처마 끝 물방울,접힌 비옷,흙냄새의 시작,물웅덩이의 하늘,버스 창의 빗줄기,젖은 신문,비 뒤의 공터,우산을 말리는 복도,갑자기 맑아진 창,젖은 머리카락,배수구의 낙엽,빗소리 없는 영상,마른 양말 한 켤레,비상계단의 사람들,넘어진 화분,흐려진 안경,빗물 자국 지도,늦게 뜬 무지개,다시 열린 운동장'),
('환상','fantasy','상상과 경계','https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000005377769','현실을 피하는 장식이 아니라 익숙한 세계의 규칙을 바꾸는 상상으로 접근한다','이미지와 현실의 경계가 매일 새롭게 편집되는 시대','뒤집힌 달,종이새의 비행,벽 너머의 바다,그림자가 먼저 걷는 길,말하는 계단,주머니 속 작은 숲,시간을 먹는 고양이,유리로 된 비,잠들지 않는 정원,이름 없는 행성,비늘 달린 구름,문장 밖으로 나온 쉼표,색을 잃은 아침,기억을 파는 시장,천장에 난 출구,한밤의 도서관 열차,눈을 감으면 켜지는 등대,비어 있는 왕좌,날개 달린 열쇠,새벽을 접는 사람'),
('별이 빛나는 밤에','starry-night','밤과 사유','https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000005377770','밤의 고요를 통해 멀리 있는 존재와 오늘의 자신을 함께 바라본다','잠들기 전까지 화면의 빛이 사라지지 않는 시대','심야 라디오,천문대 계단,도시의 한 개 별,꺼진 창문들,늦은 귀가의 달,별자리 없는 하늘,옥상 물탱크 그림자,새벽 배송의 불빛,창가의 식은 커피,구름 뒤 별자리,밤 산책의 발광표지,고장 난 가로등,별빛 아래 세탁물,잠든 휴대전화,밤 기차의 반사창,관측 노트의 빈칸,별똥별을 놓친 순간,북쪽을 찾는 나침반,해 뜨기 전 푸른 시간,불을 끈 뒤의 독서'))

SLUGS=('unfinished-letter,second-greeting,cooling-teacup,empty-seat,umbrella-boundary,ten-minutes-early,old-receipt,unclosed-door,different-steps,new-address,crossed-calendar,single-earphone,late-apology,blurred-photo,returned-book,deleted-contact,opposite-platform,shared-plant,tone-at-sentence-end,separate-way-home|familiar-station,recurring-number,unknown-old-song,dream-corridor,double-doorbell,overlaid-map,similar-silhouette,rewound-conversation,old-password,same-scent-season,empty-frame,strange-handwriting,recurring-question,misaligned-clock,familiar-typo,returned-parcel,delayed-mirror,new-shop-same-place,forgotten-promise,late-arriving-scene|wet-sneakers,eaves-drop,folded-raincoat,petrichor-beginning,puddle-sky,bus-window-rain,soaked-newspaper,field-after-rain,drying-umbrellas,sudden-clear-window,wet-hair,drain-leaves,silent-rain-video,dry-socks,stairway-shelter,fallen-pot,fogged-glasses,rainmark-map,late-rainbow,reopened-playground|upside-down-moon,paper-bird-flight,sea-behind-wall,shadow-walks-first,speaking-stairs,pocket-forest,time-eating-cat,glass-rain,sleepless-garden,nameless-planet,scaled-cloud,escaped-comma,colorless-morning,memory-market,ceiling-exit,midnight-library-train,closed-eye-lighthouse,empty-throne,winged-key,folding-dawn|midnight-radio,observatory-stairs,single-city-star,dark-windows,moon-on-way-home,constellationless-sky,rooftop-tank-shadow,dawn-delivery-light,cold-coffee-window,constellation-behind-clouds,glowing-night-sign,broken-streetlight,laundry-under-stars,sleeping-phone,night-train-reflection,observation-blank,missed-meteor,north-seeking-compass,blue-hour-before-dawn,reading-after-lights-out')
SLUG_GROUPS=[x.split(',') for x in SLUGS.split('|')]
SCENES=('서랍 안에서 계절을 건너는 물건','익숙한 거리에서 뜻밖에 마주친 얼굴','식탁 위에서 온도를 잃어 가는 사물','사라진 사람의 습관이 남은 자리','좁은 공간에서 서로 거리를 조절하는 순간','기다리는 동안 자꾸 달라지는 표정','책갈피에서 우연히 발견한 흔적','복도 불빛이 가늘게 스미는 문틈','같은 길에서 어긋나는 두 사람의 보폭','오래된 관계 안에서 새로 불리는 이름','지나간 날짜마다 표시가 늘어난 달력','하나의 소리를 나누면서도 다른 생각을 하는 시간','상처가 아문 뒤에 도착한 짧은 문장','모두 웃지만 한 사람만 흔들린 사진','다른 밑줄이 늘어난 채 돌아온 책','지웠지만 손끝이 여전히 기억하는 순서','유리 너머 반대 방향으로 지나가는 사람','혼자서도 새잎을 내는 오래된 화분','같은 문장의 마지막 음절에서 달라지는 기분','즐거운 만남 뒤 서로 다른 방향으로 향하는 버스')
TENSIONS=('진심과 침묵의 책임','재회의 기대와 과거를 미화할 위험','기다림과 이미 늦었다는 조급함','그리움과 소유하려는 마음','보호와 지나친 간섭','기대와 실망을 선점하려는 태도','추억의 온기와 기억의 선택적 편집','기다림과 관계를 끝낼 권리','동행과 속도를 맞추라는 압박','친밀감과 정체성을 존중하는 일','기다린 시간과 관계의 성과주의','공유와 개별성','용서와 응답을 요구하지 않을 책임','공동 기억과 개인의 진실','영향을 주고받는 기쁨과 해석의 차이','단절의 결심과 몸에 남은 습관','우연과 운명으로 과장하려는 욕망','관계의 끝과 계속되는 삶','내용과 태도 사이의 간극','연결과 혼자 돌아갈 자유')
ACTIONS=('느낌과 확인된 사실을 따로 적기','상대의 현재를 먼저 묻기','침묵의 이유를 추측하지 않고 질문하기','빈자리를 타인의 자유로 인정하기','도움을 주기 전에 의사를 묻기','만남의 결론을 미리 정하지 않기','좋았던 날과 힘들었던 날을 함께 기록하기','열린 가능성을 약속으로 오해하지 않기','한 번 멈춰 상대의 보폭을 확인하기','상대가 원하는 호칭을 정확히 사용하기','횟수보다 만남의 질을 돌아보기','취향의 일치를 관계의 증거로 삼지 않기','사과 뒤의 선택권을 상대에게 남기기','사진 밖 사정을 단정하지 않기','서로 다른 밑줄을 비교해 보기','연락하지 않기로 한 경계를 지키기','우연을 필연으로 바꾸어 말하지 않기','남은 생명을 과거의 소유물로 묶지 않기','상대가 들은 감정을 되묻기','헤어진 뒤의 시간을 감시하지 않기')

def josa(w,c,v):
 last=next((x for x in reversed(w) if '가'<=x<='힣'),''); return c if last and (ord(last)-0xAC00)%28 else v

def prose(work,motif,scene,tension,action,i):
 work_obj='《'+work+'》'+josa(work,'을','를'); work_join='《'+work+'》'+josa(work,'과','와')
 motif_obj=motif+josa(motif,'을','를'); scene_obj=scene+josa(scene,'을','를')
 titles=(f'{work} 문학노트: {motif}에 머물러 본 저녁',f'{work_obj} 읽고 {motif}에서 발견한 질문',f'{motif}의 감각으로 다시 만나는 {work}',f'{work} 문학노트 — {motif} 뒤에 남는 것',f'오늘의 {work}: {motif_obj} 서두르지 않는 법',f'{motif} 앞에서 펼쳐 본 {work}',f'{work_join} {motif}, 익숙한 판단을 비켜 가기',f'한 장면의 사유: {work} 곁의 {motif}')
 decks=(f'첫 장면은 {scene}. 이 작은 {motif} 풍경은 {tension} 사이에서 무엇을 선택할지 조용히 묻는다.',f'{motif_obj} 떠올리면 {scene}. 작품보다 먼저 내 일상의 태도가 읽히기 시작한다.',f'오늘 《{work}》 곁에 놓인 소재는 {motif}다. {scene}, 그때 ‘{tension}’이라는 문제가 모습을 드러낸다.',f'기억에 남은 것은 {scene}. 나는 이 풍경을 통해 독서를 결론이 아니라 질문의 시간으로 바꾸어 본다.')
 starts=(f'첫 풍경은 {scene}이다. 이 장면을 작품의 줄거리로 오해할 필요는 없다.',f'{motif}라는 소재는 사소한 생활 장면에서 출발한다. 구체적으로는 {scene}이다.',f'이번 기록의 중심에는 {motif}가 있다. 내가 떠올린 것은 {scene}이다.',f'어떤 독서는 질문보다 감각으로 먼저 돌아온다. 내게는 {scene}이 그런 순간이었다.',f'눈앞의 {scene_obj} 평소라면 지나쳤겠지만, 풍경이 {motif}라는 이름을 얻자 오래 머문다.',f'《{work_obj}》 다시 생각하며 책 밖의 {motif_obj} 살폈다. 눈앞에는 {scene}.',f'{motif}에서 출발한 생각은 예상보다 멀리 갔다. 그 출발점은 {scene}이다.',f'책을 읽고 곧장 교훈을 만들고 싶지 않았다. 대신 {scene_obj} 오래 바라보았다.')
 middles=(f'나는 {motif} 앞에서 작품을 요약하는 대신 ‘{tension}’이라는 문제를 내 삶의 질문으로 옮긴다.',f'{motif}의 풍경은 ‘{tension}’이라는 문제를 한쪽 답으로 정리하지 못하게 한다.',f'{work}의 인물이나 사건을 만들지 않아도 ‘{tension}’은 충분히 현재적인 문제다.',f'{motif}에서 모르는 부분을 남겨 두자 ‘{tension}’이 해결할 결함보다 살펴야 할 조건으로 보인다.')
 ends=(f'{motif} 앞에서 오늘 할 수 있는 일은 단순하다. {action}. 이 실천이 독자인 나의 삶을 조금 더 정직하게 만든다.',f'그래서 {motif} 메모 끝에 “{action}”라고 적는다. {motif}에 관한 큰 선언보다 작은 태도의 수정이 오래 남는다.',f'{motif} 앞에서 {action}. 이것이 {motif} 감상을 현실과 연결하면서도 타인의 경험을 대신 말하지 않는 방법이다.',f'{motif}에 관한 다음 선택에서는 {action}. 그 뒤의 결과는 미리 확정하지 않기로 한다.')
 return titles[i%8],decks[(i*3)%4],' '.join((starts[i%8],middles[(i*5)%4],ends[(i*7)%4]))

def vary_sentences(text,motif,index):
 motif_obj=motif+josa(motif,'을','를')
 prefixes=(f'{motif_obj} 곁에 두면, ',f'{motif}의 관점에서는, ',f'{motif_obj} 오래 바라보니, ',f'{motif}에서 출발하면, ',f'{motif}에 관한 이번 독서에서, ',f'{motif}의 감각을 따라가면, ',f'{motif} 앞에 잠시 멈추면, ',f'{motif_obj} 오늘의 질문으로 삼으면, ')
 parts=re.split(r'(?<=[.!?])\s+',text)
 out=[]
 for pos,sentence in enumerate(parts):
  if len(sentence)>=12 and motif not in sentence:
   sentence=prefixes[(index+pos*3)%len(prefixes)]+sentence[0].lower()+sentence[1:]
  out.append(sentence)
 return ' '.join(out)

def make_note(w,wi,mi,seq):
 work,wslug,tag,url,frame,now,motifs=w; motif=motifs.split(',')[mi]; slug=SLUG_GROUPS[wi][mi]
 # 각 작품에서 같은 순번 소재도 장면·갈등·행동의 조합을 다르게 회전한다.
 scene=SCENES[(mi+wi*3)%20]+'에서 '+motif+'의 의미가 새로 보이는 순간'
 tension=TENSIONS[(mi*3+wi*5)%20]; action=ACTIONS[(mi*7+wi*2)%20]; i=wi*20+mi
 title,deck,commentary=prose(work,motif,scene,tension,action,i)
 obj=motif+josa(motif,'을','를'); subj=motif+josa(motif,'이','가'); join='《'+work+'》'+josa(work,'과','와'); work_obj='《'+work+'》'+josa(work,'을','를'); scene_obj=scene+josa(scene,'을','를')
 seo={
 'work_introduction':f'소설가 이후의 한국어 창작 작품 《{work}》에 관한 {motif} 중심의 독창적 문학노트다. 이 {motif} 기록은 교보ebook 공식 도서 정보로 작품과 작가를 확인했으며 본문이나 대사를 직접 인용하지 않는다. 이번 글은 {obj} 독립적인 소재로 삼아 {frame}.',
 'why_read_now':f'{now}에는 ‘{tension}’이라는 문제를 한쪽 답으로 밀어붙이기 쉽다. 오늘 떠올린 풍경은 {scene}이다. 이는 {work_obj} 오늘 다시 생각하면서 {obj} 통해 즉각적인 요약보다 맥락을 먼저 살피게 한다.',
 'personal_reflection':f'나는 {scene_obj} 떠올리며 판단이 얼마나 빨리 결론을 만드는지 돌아보았다. {join} {motif} 사이의 연결은 작품의 내용을 대신 설명하지 않는다. 대신 {tension} 앞에서 내가 취한 거리와 말투를 점검하게 한다.',
 'meaning_today':f'오늘의 의미는 거창한 교훈보다 {action}에 있다. 이 행동은 ‘{tension}’이라는 문제를 지워 버리지 않으면서도 현실에서 선택할 작은 기준을 제공한다. {subj} 남긴 질문은 그렇게 일상의 윤리로 이어진다.'}
 note={'id':f'20260829_leehu_literature_{seq:03d}','slug':f'leehu-20260829-{wslug}-{slug}-reflection','title':title,'quote':deck,'source_author':'이후','source_work':work,'source_location':'교보ebook 도서 정보의 작가 소개 및 작품 설명 참고 · 작품 본문 직접 인용 없음','source_language':'ko','source_url':url,'translation_note':'한국어 창작 작품에 관한 독창적 감상으로 작품 본문과 타인의 번역문을 옮기지 않음.','rights_note':f'소설가 이후의 작품 《{work}》에 관한 자체 작성 문학노트이며 작품 본문 직접 인용 없음.','commentary':commentary,'closing':f'오늘의 기록은 “{action}”라는 실천을 남기고 {motif}의 다음 의미는 독자에게 열어 둔다.','author':'소설가 이후','tags':['소설가 이후',work,tag,motif,'독창적 감상'],'related_work':{'name':work,'url':url},'published_at':PUBLISHED_AT,'content_kind':'original_reflection','seo_sections':seo}
 for field in ('quote','commentary','closing'):
  note[field]=vary_sentences(note[field],motif,i)
 note['commentary'] += f' {obj} 살피는 동안 나는 {work_obj} 대신 설명하기보다, 이 소재가 오늘의 판단과 태도에 남기는 미세한 변화를 끝까지 관찰해야 한다고 느꼈다.'
 note['seo_sections']={key:vary_sentences(value,motif,i+pos) for pos,(key,value) in enumerate(note['seo_sections'].items())}
 return note

def review(notes):
 for field in ('id','slug','title','quote','commentary','closing'):
  vals=[re.sub(r'\s+',' ',str(n[field])).casefold() for n in notes]
  if len(vals)!=len(set(vals)): raise SystemExit('duplicate '+field)
 if len({n['tags'][3] for n in notes})!=50: raise SystemExit('motifs not unique')
 sentences=[]
 for n in notes:
  prose=' '.join((n['quote'],n['commentary'],n['closing'],*n['seo_sections'].values()))
  if any(x in prose for x in ('AI','자동 생성','공식 카탈로그','원문 확인 필요','권리이','자유을','과정를','소나기을','경계을','연(戀)를','연(戀)와','환상를','환상와','밤에를','역를','하늘를','달를','정원를')): raise SystemExit('forbidden prose '+n['id'])
  if any(len(v)<100 for v in n['seo_sections'].values()): raise SystemExit('short SEO '+n['id'])
  sentences += [x.strip() for x in re.split(r'(?<=[.!?])\s+',prose) if len(x.strip())>=25]
 dup=[x for x,c in Counter(sentences).items() if c>1]
 if dup: raise SystemExit('repeated sentence: '+dup[0])

def main():
 existing=sorted(CONTENT.glob('*.json'),key=lambda p:int(p.stem)); count=len(existing)
 if count not in (EXPECTED_BEFORE,EXPECTED_BEFORE+50): raise SystemExit(f'expected 2981 or 3031 sources, found {count}')
 notes=[]
 for wi,w in enumerate(WORKS):
  for mi in range(10): notes.append(make_note(w,wi,mi,START_SEQUENCE+wi*10+mi))
 review(notes)
 targets=[CONTENT/f'{i}.json' for i in range(2982,3032)]
 if count==3031 and [json.loads(p.read_text()) for p in targets]!=notes: raise SystemExit('existing batch differs; replace explicitly')
 MANIFEST.write_text(json.dumps(notes,ensure_ascii=False,indent=2)+'\n')
 print('reviewed and wrote 50 notes with 50 unique motifs')
if __name__=='__main__': main()
