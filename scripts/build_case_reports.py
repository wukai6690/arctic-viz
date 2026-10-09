"""Build the three downloadable, sourced reports from the same website content."""
import hashlib,json,sys,re
from pathlib import Path
from html import escape
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,PageBreak,KeepTogether
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from PIL import Image as PILImage
from src.deep_case_content import case_report_text,load_deep_cases
from src.mosaic_research import mosaic_report_data,load_mosaic,DATA
from src.research_catalog import project_media

OUT=ROOT/'static/reports';OUT.mkdir(parents=True,exist_ok=True)
pdfmetrics.registerFont(TTFont('YaHei','C:/Windows/Fonts/msyh.ttc',subfontIndex=0))
pdfmetrics.registerFont(TTFont('YaHeiBold','C:/Windows/Fonts/msyhbd.ttc',subfontIndex=0))
BODY=ParagraphStyle('body',fontName='YaHei',fontSize=10,leading=17,textColor=colors.HexColor('#304d43'),spaceAfter=7,wordWrap='CJK')
SMALL=ParagraphStyle('small',parent=BODY,fontSize=8,leading=13,textColor=colors.HexColor('#52685d'))
H1=ParagraphStyle('h1',parent=BODY,fontName='YaHeiBold',fontSize=24,leading=36,spaceAfter=16)
H2=ParagraphStyle('h2',parent=BODY,fontName='YaHeiBold',fontSize=15,leading=24,spaceBefore=17,spaceAfter=10,keepWithNext=True)
H3=ParagraphStyle('h3',parent=BODY,fontName='YaHeiBold',fontSize=11,leading=18,spaceBefore=8,spaceAfter=7,keepWithNext=True)
SECTIONS={'研究问题','时间、空间与观察单位','案例概述','目前能够支持的判断','量化事实及统计口径','历史时间线','任务、能力、参与方与可观察结果','历史股权关系','机制解释与证据','替代解释与下一步核对','资料局限','中国参与的后续研究问题','方法说明','来源登记','真实船位与同期冰情','任务对照','目前可支持的认识','仍需验证','资料覆盖与处理方法'}

def para(text,style=BODY):return Paragraph(escape(str(text)),style)
def picture(path,max_width=475,max_height=260):
    with PILImage.open(path) as im:w,h=im.size
    ratio=min(max_width/w,max_height/h)
    return Image(str(path),width=w*ratio,height=h*ratio,hAlign='LEFT')

def footer(canvas,doc):
    canvas.saveState();canvas.setStrokeColor(colors.HexColor('#b8cbbb'));canvas.line(50,48,545,48)
    canvas.setFont('YaHei',8);canvas.setFillColor(colors.HexColor('#52685d'))
    canvas.drawString(50,33,'北极观察 · 地理大创 · 案例资料报告 / 2026-10-10')
    canvas.drawRightString(545,33,str(doc.page));canvas.restoreState()

def mosaic_text():
    report=mosaic_report_data();data=load_mosaic();m=report['manifest']
    out=['MOSAiC：持续观测的设备、环境与协作条件','基于五段真实船位与 14 个日期的官方海冰图', '', '研究问题','持续观测如何依靠船舶平台、仪器设备、机构分工与资料共享？本报告以位置、日期和可核对产出组织问题，尚不估计合作的因果效果。', '', '资料覆盖与处理方法',f"航次范围：{m['start']}—{m['end']}（UTC）。共 {m['track_rows']:,} 条船位、{m['daily_rows']} 个日期。",m['map_method'],m['ice_selection_rule'],'船位采用 WGS84 经纬度。每日选择最接近 12:00 的真实点，不插值生成正午位置。冰图标题日期与图内船位图例时间可能相差一天，两者不强行视为同刻。','海冰密集度不是冰厚或航行风险；灰色缺测不能解释为无冰。船舶航迹包含自主航行与随冰漂流，不能把全部路径称为浮冰漂移。','', '任务对照']
    source_ids={s['id']:i+1 for i,s in enumerate(report['sources'])}
    for r in report['tasks']:
        out += [r['task'],'设备：'+r['equipment'],'负责机构：'+r['institution'],'资料产出：'+r['output'],'本站状态：'+r['evidence'],'依据：'+' '.join(f'[{source_ids[x]}]' for x in r['source_ids'])]
    out+=['','目前可支持的认识',*report['facts'],report['interpretation'],'公开仪器分工与实际数据产出为进一步追查协作条件提供线索；尚不能据此断言国家关系改善或功能性安全已实现。','','仍需验证',*report['gaps'],'访谈与实地调研尚未开展。需要团队继续复核公开资料与解释，并记录实际研究过程。','','来源登记']
    for i,s in enumerate(report['sources'],1):out += [f"[{i}] {s['title']} · {s['publisher']}",s.get('citation',''),'定位：'+s['locator'],s['url'],s['notice']]
    return '\n'.join(out)

def build(cid,text):
    lines=text.splitlines();title=escape(lines[0]).replace('：','：<br/>',1)
    story=[para('北极观察 / 案例研究',SMALL),Spacer(1,14),Paragraph(title,H1),para(lines[1],BODY),para('资料整理版 · 2026-10-10 · 研究事实与解释边界分别呈现',SMALL),Spacer(1,12)]
    photos=project_media().get(cid,[])
    if photos:
        p=photos[0];path=ROOT/'static/places'/Path(p['src']).name
        story += [picture(path),Spacer(1,6),para(p['caption']+'；'+p['author']+'；'+p['date']+'；'+p['license'],SMALL),para('照片为场景说明，不能替代对应日期的观测或性能记录。',SMALL),para('照片出处：'+p['source_url'],SMALL)]
    story.append(PageBreak())
    if cid=='mosaic':
        story += [para('真实船位与同期冰情',H2),para('网站可按日期查看真实航迹，并下载相应证据包。以下保留同一产品的两个预选日期，说明季节背景；不从图片推算船边数值。')]
        ice=load_mosaic()['ice']
        for day in ['2019-10-15','2020-08-15']:
            r=next(r for r in ice if r['date']==day)
            story += [para(day,H3),picture(DATA/r['path'],475,330),para('Meereisportal / AWI / 不来梅大学 IUP；AMSR2 / ASI，6.25 km 网格，海冰密集度（%）。图内船位标记时间依原图图例。',SMALL)]
        story.append(PageBreak())
    in_sources=False;section='';block=[]
    def flush():
        if block:
            group=list(block)
            if story and isinstance(story[-1],Paragraph) and story[-1].style.name=='h2':group.insert(0,story.pop())
            story.append(KeepTogether(group));block.clear()
    for line in lines[2:]:
        if not line.strip():continue
        if line in SECTIONS:
            flush();section=line
            if line=='来源登记':in_sources=True
            story.append(para(line,H2))
        elif in_sources:
            if re.match(r'^\[\d+\]',line):flush()
            block.append(para(line,SMALL))
        elif section in ['量化事实及统计口径','任务、能力、参与方与可观察结果','任务对照']:
            if not line.startswith(('含义：','边界：','能力：','参与方：','观察结果：','设备：','负责机构：','资料产出：','本站状态：','依据：')):flush()
            block.append(para(line,SMALL if line.startswith('边界：') else BODY))
        else:story.append(para(line,SMALL if line.startswith(('边界：','定位：','https://')) else BODY))
    flush()
    path=OUT/f'{cid}-case-report.pdf'
    SimpleDocTemplate(str(path),pagesize=(595.28,841.89),rightMargin=50,leftMargin=50,topMargin=47,bottomMargin=65,title=lines[0],author='北极观察 · 案例资料整理',pageCompression=1).build(story,onFirstPage=footer,onLaterPages=footer)
    (OUT/f'{cid}-case-report.txt').write_text(text,encoding='utf-8')
    return dict(id=cid,file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),bytes=path.stat().st_size)

if __name__=='__main__':
    reports=[build(cid,mosaic_text() if cid=='mosaic' else case_report_text(cid)) for cid in ['mosaic','asbm','yamal']]
    (OUT/'manifest.json').write_text(json.dumps({'generated_at':'2026-10-10','reports':reports},ensure_ascii=False,indent=2),encoding='utf-8')
    for report in reports:print(report['file'],report['bytes'])
