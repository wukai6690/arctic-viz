import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
path=ROOT/'data/editorial/place_enrichment/selected.json'
items=json.loads(path.read_text(encoding='utf-8'))
extras=[
 ('tiksi','52492382','季克西城镇与周边地貌','社区生活','聚落实景，拍摄年代见来源。'),
 ('tromso','129172245','特罗姆瑟大桥与大陆一侧的北极教堂','社区生活','城市跨海联系与公共建筑，不是科研设施。'),
 ('reykjavik','93703293','雷克雅未克 Tjörnin 湖旁的学校与城市建筑','社区生活','城市湖区与公共生活场景。'),
 ('helsinki','73602559','赫尔辛基市场广场与南港','社区生活','海岸城市生活景观。'),
 ('helsinki','152984827','赫尔辛基市场广场保留的港口铁路轨道（2024 年）','历史影像','现地拍摄的旧铁路遗迹，非现役货运线路。'),
 ('sabetta','118058857','萨别塔 LNG 设施','产业现场','萨别塔能源项目现场；设施能力以项目材料为准。'),
 ('bremerhaven','152465429','不来梅港城市建筑与滨水环境（2024 年）','社区生活','港城建筑景观，非科考船现场。'),
]
present={i['id'] for i in items}
items += [dict(owner=o,id=i,caption=c,topic=t,scope=s) for o,i,c,t,s in extras if i not in present]
path.write_text(json.dumps(items,ensure_ascii=False,indent=2),encoding='utf-8')
print('SELECTED',len(items))
