"""Apply conservative subject categories to the already reviewed image captions."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OVERRIDES={'1137880':'自然环境','54496510':'自然环境','47333023':'自然环境',
 '155703338':'交通与港口','149075421':'社区生活','34000648':'社区生活',
 '52595563':'自然环境','31385247':'社区生活','2939106':'自然环境',
 '1848207':'设施全景','131499854':'设施全景','130459559':'科研设施',
 '128839035':'产业现场','137761343':'产业现场','171777729':'自然环境',
 '24587242':'设施全景','139263028':'科研设施','139262473':'科研设施'}
def topic(photo):
    if photo.get('topic'):return photo['topic']
    if photo['id'] in OVERRIDES:return OVERRIDES[photo['id']]
    text=photo['caption']
    for terms,category in [(['历史照片','旧址','已停用'],'历史影像'),
        (['造船厂','工厂','厂区','焊接','铁矿','装船'],'产业现场'),
        (['观测','科考','科研','实验','天线','卫星','火箭','气球','研究设施'],'科研设施'),
        (['港','码头','机场','船','轮','飞机','直升','拖船'],'交通与港口'),
        (['教堂','街','城区','市中心','中心','市政厅','聚落','城镇','社区','木屋','标识','建筑'],'社区生活'),
        (['峡湾','海岸','冰盖','冰山','海冰','雪地','苔原','林地','山','谷地','日落','秋色','极光','岛'],'自然环境')]:
        if any(term in text for term in terms):return category
    return '设施全景'
for filename in ['places.json','project_media.json']:
    path=ROOT/'data/reference'/filename;data=json.loads(path.read_text(encoding='utf-8'))
    photos=[p for place in data['places'] for p in place['photos']] if filename=='places.json' else [p for group in data.values() for p in group]
    for photo in photos:photo['topic']=topic(photo)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
print('Tagged published photos')
