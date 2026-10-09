"""Editorial selection: exact Commons results inspected for subject and location."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/editorial'
# id, Chinese, English, region, category, photograph selection, description, reference.
specs=[
('longyearbyen','朗伊尔城','Longyearbyen','斯瓦尔巴','城市与聚落',[('longyearbyen',2,'从 Hiorthfjellet 望向朗伊尔城'),('longyearbyen',7,'朗伊尔城港内的 Kronprins Haakon 科研船'),('longyearbyen',12,'朗伊尔城港湾')], '斯瓦尔巴的聚落与港口。图集将居住空间、港湾和科研船舶放在同一地点档案中。','https://www.ksat.no/news/news-archive/2023/spectacular-drone-footage-from-svalsat-the-ksat-svalbard-ground-station/'),
('nyalesund','新奥尔松','Ny-Ålesund','斯瓦尔巴','科研观测',[('nyalesund',9,'德国观测设施外景 · 新奥尔松'),('nyalesund',2,'新奥尔松中国科考站入口'),('nyalesund',1,'新奥尔松周边峡湾与雪地')], '位于斯瓦尔巴的科研聚落，多国研究机构在这里开展观测。AWIPEV 专题说明其中的法德联合研究关系。','https://nyalesundresearch.no/'),
('tromso','特罗姆瑟','Tromsø','北欧','港口与航道',[('tromso',1,'特罗姆瑟港湾 · 2014 年'),('tromso',2,'停靠 Prostneset 的 Vesterålen 轮'),('tromso',12,'从山上俯瞰特罗姆瑟')], '挪威北部港口城市。MOSAiC 考察在这里准备并启航，港口也是认识北极科研后勤的入口。','https://www.awi.de/ueber-uns/service/presse/presse-detailansicht/polarstern-startet-richtung-arktis.html'),
('svalsat','斯瓦尔巴卫星站','SvalSat','斯瓦尔巴','空间设施',[('svalsat',2,'Platåberget 山上的 SvalSat 卫星站'),('svalsat',5,'雪地中的天线罩 · 2015 年'),('svalsat',4,'用于教学与访问展示的天线内部')], '朗伊尔城附近的极轨卫星地面设施。地点档案展示公开的站区和天线照片，不表示卫星当前所在位置。','https://www.ksat.no/news/news-archive/2023/spectacular-drone-footage-from-svalsat-the-ksat-svalbard-ground-station/'),
('esrange','埃斯兰航天中心','Esrange Space Center','北欧','空间设施',[('esrange',3,'埃斯兰的抛物面天线'),('esrange',2,'MAPHEUS-3 探空火箭发射 · 2012 年'),('esrange',10,'埃斯兰设施内的安全装备')], '基律纳附近的航天与地面接收设施。SSC 的 Kinuvik 方案把这里与加拿大伊努维克地面站配合使用。','https://sscspace.com/services/satellite-ground-stations/our-stations/esrange-ground-station/'),
('murmansk','摩尔曼斯克','Murmansk','俄罗斯北部','港口与航道',[('murmansk',1,'摩尔曼斯克港 · 2022 年'),('murmansk',5,'从城区望向港区 · 2014 年'),('murmansk',11,'列宁号附近的港湾全景 · 2022 年')], '科拉湾沿岸的港口城市。照片记录港区、城区与海湾的空间关系，可与周边科拉半岛档案对照。','https://commons.wikimedia.org/wiki/Category:Port_of_Murmansk'),
('sabetta','萨别塔','Sabetta','俄罗斯北部','港口与航道',[('sabetta',1,'萨别塔冰封港区内的 Tor 破冰船'),('sabetta',5,'Valeri Vasiliev 轮驶入萨别塔港'),('sabetta',3,'萨别塔机场停机坪')], '鄂毕湾沿岸的港口与后勤节点。亚马尔 LNG 项目的历史资料将港口、冰级船舶和跨国投资联系在一起。','https://totalenergies.com/newsroom/yamal-lng-project-begins-gas-exports/?lang=eng'),
('tiksi','季克西','Tiksi','俄罗斯北部','港口与航道',[('tiksi',1,'季克西聚落全景'),('tiksi',3,'季克西沿海冰情与山地 · 2015 年'),('tiksi',6,'季克西附近的气象观测设施')], '拉普捷夫海沿岸的聚落与港口节点。城市和气象站照片帮助认识东北航道沿岸的环境。','https://commons.wikimedia.org/wiki/Category:Tiksi'),
('pevek','佩韦克','Pevek','俄罗斯北部','港口与航道',[('pevek',1,'佩韦克港码头'),('pevek',2,'从南侧望向佩韦克'),('pevek',3,'从 Paakinay 山坡望向佩韦克')], '楚科奇北岸的港口城市。此处展示公开港区与聚落实景，作为北极沿岸交通研究的地理背景。','https://commons.wikimedia.org/wiki/Category:Pevek'),
('reykjavik','雷克雅未克','Reykjavík','冰岛','港口与航道',[('reykjavik',1,'雷克雅未克老港'),('reykjavik',3,'老港码头与船舶'),('reykjavik',2,'雷克雅未克港内的 Magni 轮 · 2017 年')], '冰岛首都的港口节点。记录老港、工作船和城市海岸，提供北大西洋与北极相关活动的地域背景。','https://commons.wikimedia.org/wiki/Category:Port_of_Reykjav%C3%ADk'),
('akureyri','阿克雷里','Akureyri','冰岛','港口与航道',[('akureyri',1,'阿克雷里港湾 · 2016 年'),('akureyri',4,'从岸边望向阿克雷里港'),('akureyri',9,'阿克雷里城区与港口')], '冰岛北部峡湾中的港口城市。照片呈现港湾、城区和周围地形，作为北大西洋交通节点的补充。','https://commons.wikimedia.org/wiki/Category:Akureyri'),
('cambridgebay','剑桥湾','Cambridge Bay · Iqaluktuuttiaq','加拿大北部','科研观测',[('cambridgebay',1,'剑桥湾聚落航拍'),('cambridgebay',7,'剑桥湾街区与环境'),('cambridgebay',9,'剑桥湾日落')], '加拿大努纳武特地区的社区，也是 CHARS 科研站所在地。照片为社区环境，不冒充科研站内部或研究现场。','https://www.canada.ca/en/polar-knowledge/CHARScampus.html'),
('inuvik','伊努维克','Inuvik','加拿大北部','城市与聚落',[('inuvik',3,'秋色中的伊努维克周边'),('inuvik',5,'伊努维克城镇中心'),('inuvik',9,'晚间阳光下的伊努维克城区')], '加拿大西北地区的社区，周边设有极轨卫星接收设施。此档案照片展示社区，技术专题另列地面站的原始资料。','https://natural-resources.canada.ca/science-data/science-research/research-centres/inuvik-satellite-station-facility'),
('utqiagvik','乌特恰维克','Utqiaġvik · Barrow','阿拉斯加','城市与聚落',[('utqiagvik',1,'乌特恰维克聚落'),('utqiagvik',2,'乌特恰维克北冰洋海岸'),('utqiagvik',7,'乌特恰维克鲸骨拱门')], '阿拉斯加北岸社区，旧名 Barrow。保留海岸与聚落实景，为北极居民生活及环境研究提供地点背景。','https://commons.wikimedia.org/wiki/Category:Utqiagvik,_Alaska'),
('nome','诺姆','Nome','阿拉斯加','港口与航道',[('nome',1,'诺姆港与防波堤航拍'),('nome',12,'前往诺姆港的 Renda 油轮 · 2012 年'),('nome',4,'诺姆港历史照片 · 约 1899 年')], '阿拉斯加西部、白令海峡附近的港口节点。历史与近代照片分别标注日期，不代表现有港区工程已经完成。','https://www.nomealaska.org/1359/Port-of-Nome'),
('churchill','丘吉尔','Churchill','加拿大北部','港口与航道',[('churchill',1,'从港口望向丘吉尔镇'),('churchill_extra',1,'丘吉尔镇 · 2010 年'),('churchill_extra',4,'丘吉尔河与岸线')], '哈得孙湾沿岸的港口聚落。位置在北极圈以南，作为北方交通的外围节点纳入。','https://commons.wikimedia.org/wiki/Category:Churchill,_Manitoba'),
('resolute','雷索卢特','Resolute · Qausuittuq','加拿大北部','城市与聚落',[('resolute',1,'雷索卢特湾 · 1997 年'),('resolute',12,'向南望向雷索卢特湾'),('resolute',9,'雷索卢特社区')], '加拿大北极群岛中的社区。湾岸、机场周边与聚落实景为认识群岛交通环境提供背景。','https://commons.wikimedia.org/wiki/Category:Resolute,_Nunavut'),
('bremerhaven','不来梅港','Bremerhaven','关联产业城市','关联产业',[('bremerhaven',1,'母港内的 Polarstern 科研破冰船'),('bremerhaven',3,'Polarstern 与拖船'),('bremerhaven',7,'船坞中的 Polarstern')], '德国北海沿岸港口，Polarstern 的母港。作为极地科研后勤关联城市显示，不属于北极圈内地点。','https://www.awi.de/en/focus/mosaic-expedition.html'),
('helsinki','赫尔辛基','Helsinki','关联产业城市','关联产业',[('helsinki_extra',1,'Katajanokka 停泊的芬兰破冰船 · 2026 年'),('helsinki_extra',3,'从 Korkeasaari 望向破冰船泊位'),('helsinki_extra',11,'Urho 与 Kontio 破冰船')], '芬兰南部的海事产业城市。图集展示公开的破冰船泊位，用作冰区船舶专题的产业背景，不表示这些船参与了其他专题项目。','https://commons.wikimedia.org/wiki/Category:Icebreakers_in_Helsinki'),
('shanghai','上海 · 江南造船','Shanghai · Jiangnan Shipyard','关联产业城市','关联产业',[('shanghai_extra',3,'长兴岛江南造船厂全景'),('shanghai_extra',7,'长兴岛厂区航拍 · 2023 年'),('shanghai_extra',10,'江南造船厂焊接作业历史照片 · 1965 年')], '雪龙2号的建造关联城市。照片展示厂区和历史作业；地图使用城市级位置，船舶专题另列香港访问期间拍摄的雪龙2号照片。','https://dnr.gxzf.gov.cn/xwzx/gnzx/t16076657.shtml'),
]
places=[]
for pid,name,en,region,category,selections,description,url in specs:
    files=[]
    for source,index,caption in selections:
        found=json.loads((OUT/'research'/(source+'-summary.json')).read_text(encoding='utf-8'))[index-1]
        files.append([found['title'],caption])
    places.append(dict(id=pid,name=name,english=en,region=region,category=category,kind=category,description=description,reference_url=url,
        location_note='地点中心示意位置；图片拍摄对象和日期见图注，不代表新闻事件的精确坐标。',files=files))
(OUT/'atlas_additions.json').write_text(json.dumps(places,ensure_ascii=False,indent=2),encoding='utf-8')
# A ship photographed in Hong Kong belongs to the vessel dossier, not Shanghai's place gallery.
results=json.loads((OUT/'research/shanghai-summary.json').read_text(encoding='utf-8'))
media={'xuelong2':[[results[i]['title'],caption] for i,caption in [(0,'雪龙2号访问香港维多利亚港 · 2024 年'),(3,'雪龙2号烟囱与上层建筑 · 香港访问期间'),(1,'雪龙2号船尾与直升机甲板 · 香港访问期间')]]}
(OUT/'project_media_selections.json').write_text(json.dumps(media,ensure_ascii=False,indent=2),encoding='utf-8')
print('Selected',len(places),'places and 3 vessel photographs')
