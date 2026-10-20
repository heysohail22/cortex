"""Render a presentation overview locally: python3 backend/docs/diagrams/render_workflow.py."""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

im=Image.new('RGB',(2000,2520),'#f1f5f9'); d=ImageDraw.Draw(im)
fp='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
def font(n): return ImageFont.truetype(fp,n)
def text(x,y,s,size=27,color='#334155',anchor=None): d.text((x,y),s,font=font(size),fill=color,anchor=anchor)
def card(x,y,w,h,title,lines,color='#2563eb'):
 d.rounded_rectangle((x,y,x+w,y+h),radius=23,fill='white',outline='#cbd5e1',width=2)
 d.rounded_rectangle((x,y,x+9,y+h),radius=4,fill=color)
 text(x+30,y+23,title,30,color)
 for i,line in enumerate(lines): text(x+30,y+75+i*39,line,25)
def arrow(x,y,x2,y2,label=''):
 d.line((x,y,x2,y2),fill='#64748b',width=5)
 d.polygon([(x2,y2),(x2-11,y2-17),(x2+11,y2-17)],fill='#64748b')
 if label: text((x+x2)/2+20,(y+y2)/2,label,23)
text(100,55,'CORTEX',54,'#0f172a')
text(100,125,'How a question becomes an answer',39,'#0f172a')
text(100,187,'Simplified overview of the current workflow · read from top to bottom',26)
card(100,250,1800,150,'1   RECEIVE THE QUESTION',['API checks: local pattern checks and PII redaction.'],'#475569')
arrow(1000,400,1000,445)
card(100,445,1800,190,'2   JEV CHOOSES THE PATH AND CHECKS SAFETY',['Safe question → documents, live web information, or general knowledge.', 'Unsafe, uncertain or failed assessment → controlled response; no tool execution.'],'#d97706')
arrow(1000,635,1000,695)
# Three parallel routes
card(100,695,560,200,'A   DOCUMENT QUESTION',['Search your vector database.', 'Jev selects useful passages', 'and checks evidence sufficiency.'],'#059669')
card(720,695,560,200,'B   LIVE WEB QUESTION',['Search the web.', 'Use the returned web evidence', 'to prepare a grounded answer.'],'#0891b2')
card(1340,695,560,200,'C   GENERAL QUESTION',['Generate a direct answer.', 'No retrieval is needed.', 'Source verification is skipped.'],'#7c3aed')
arrow(380,895,380,945)
card(100,945,1180,265,'3   RESOLVE DOCUMENT EVIDENCE',['Enough evidence → continue to generation.', 'Partial or no evidence → one targeted rewrite + retrieval retry.', 'Still partial → answer only the supported part, or clarify.', 'No evidence / provider failure → missing-evidence or unavailable response.'],'#059669')
card(1340,945,560,265,'FAST DIRECT PATH',['General answers go directly', 'to final output checks.', '', 'They are not marked as', 'verified against sources.'],'#7c3aed')
# Scope policy note
card(100,1250,1800,145,'WEB SUPPLEMENTATION IS OPTIONAL',['Document gaps use web search only with explicit trusted public policy + an approved query.'],'#0891b2')
arrow(690,1395,690,1450,'Document / web evidence')
card(100,1450,1180,195,'4   GENERATE A GROUNDED DRAFT',['Give the model a limited, fixed evidence snapshot.', 'The draft links factual claims to document or web evidence.', 'Keep the draft internal until verification finishes.'],'#7c3aed')
card(1340,1450,560,195,'CONTROLLED RESPONSES',['Refusal, clarification, missing', 'evidence and unavailable', 'responses go to output checks.'],'#dc2626')
arrow(690,1645,690,1700)
card(100,1700,1180,190,'5   VERIFY THE DRAFT',['An independent judge checks the answer and its claims', 'against the exact evidence used during generation.', 'SUPPORTED → release the approved answer to output checks.'],'#d97706')
card(1340,1700,560,190,'IF VERIFICATION FAILS',['UNSUPPORTED → repair once,', 'then verify again.', 'UNKNOWN / still fails → fallback.'],'#dc2626')
arrow(690,1890,690,1960)
card(100,1960,1800,195,'6   FINAL OUTPUT CHECKS',['All response paths meet here: grounded, direct, controlled and fallback.', 'Scrub secrets and validate citations. Changes to a verified answer invalidate its approval.', 'Send the final answer or controlled response to the user.'],'#2563eb')
arrow(1000,2155,1000,2210)
d.rounded_rectangle((580,2210,1420,2300),radius=35,fill='#2563eb')
text(1000,2255,'USER RECEIVES THE RESPONSE',30,'white','mm')
text(100,2355,'LIMITS THAT KEEP THE FLOW BOUNDED',26,'#0f172a')
text(100,2403,'At most one retrieval correction · one shared answer repair · bounded context',25)
text(100,2450,'Presentation overview: terminal paths are described in cards to avoid crossing arrows.',22,'#64748b')
im.save(Path(__file__).with_name('cortex_workflow.png'))
