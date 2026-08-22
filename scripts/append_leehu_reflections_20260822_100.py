#!/usr/bin/env python3
import json
from pathlib import Path
import append_leehu_reflections_20260821 as base

ROOT=Path(__file__).resolve().parents[1]
CONTENT=ROOT/'content'/'literature'
TOPICS=[
('인물의 침묵이 장면을 바꾸는 순간','침묵 뒤의 장면','침묵','장면'),('첫 문장이 독자를 부르는 방식','독자를 부르는 첫 문장','첫문장','독자'),('낯선 공간을 이야기로 기억하는 법','공간의 기억','공간','기억'),('갈등을 설명하지 않고 보여주는 장면','보이는 갈등','갈등','묘사'),('인물의 선택이 서사를 움직이는 이유','선택의 서사','선택','서사'),('오래된 물건에 시간을 담는 방법','물건에 담긴 시간','사물','시간'),('후회가 인물을 성장시키는 방향','후회의 방향','후회','성장'),('반복되는 일상에서 변화를 찾는 눈','일상의 변화','일상','변화'),('독자의 상상에 맡겨야 하는 여백','상상의 여백','상상','여백'),('감정의 이름을 늦게 부르는 문장','늦게 불린 감정','감정','문장'),('떠나는 사람과 남는 사람의 거리','떠남과 남음','이별','거리'),('사소한 오해가 관계를 흔드는 방식','오해의 파문','오해','관계'),('배경의 날씨가 인물에게 미치는 힘','날씨와 인물','날씨','인물'),('대사의 생략이 만드는 긴장','생략된 대사','대사','긴장'),('결말 이후를 생각하게 하는 이야기','결말 이후','결말','여운'),('인물의 습관으로 성격을 드러내기','습관의 서사','습관','성격'),('한 장면을 여러 시선으로 읽는 법','여러 시선의 장면','시선','해석'),('시간의 순서를 바꾸어 기억을 쓰기','뒤섞인 시간','시간','기억'),('설명보다 정확한 하나의 이미지','하나의 이미지','이미지','묘사'),('쓰지 않은 문장이 남기는 의미','쓰지 않은 문장','문장','의미')]

def main():
 files=list(CONTENT.glob('*.json'))
 if len(files) not in (2171,2271): raise SystemExit(f'expected 2171 or 2271, found {len(files)}')
 n=2172
 for wi,work in enumerate(base.WORKS):
  for ti,topic in enumerate(TOPICS):
   ordinal=wi*len(TOPICS)+ti+1; seq=ordinal+50
   d=base.note_for(ordinal,work,topic)
   d['id']=f'20260822_leehu_literature_{seq:03d}'
   parts=d['slug'].split('-'); parts[2]=f'{seq:03d}'; d['slug']='-'.join(parts)
   d['published_at']='2026-08-22T14:00:00+09:00'
   (CONTENT/f'{n:03d}.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); n+=1
 print('created 100 notes')
if __name__=='__main__': main()
