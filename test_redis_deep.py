# -*- coding: utf-8 -*-
"""Redis 深度讲解视频"""
import sys, json
sys.path.insert(0, '.')

def mock_llm(prompt):
    scenes = {
        '什么是Redis': {
            'objects': [
                {'keyword': 'database', 'x': 500, 'y': 200, 'scale': 4.5},
                {'keyword': 'lightbulb', 'x': 1100, 'y': 150, 'scale': 2.0}
            ],
            'flows': [{'from': 0, 'to': 1, 'label': 'fast'}]
        },
        '为什么快': {
            'objects': [
                {'keyword': 'brain', 'x': 400, 'y': 180, 'scale': 4.0},
                {'keyword': 'gear', 'x': 900, 'y': 250, 'scale': 3.5},
                {'keyword': 'lightbulb', 'x': 1400, 'y': 180, 'scale': 2.0}
            ],
            'flows': [
                {'from': 0, 'to': 1, 'label': 'design'},
                {'from': 1, 'to': 2, 'label': 'result'}
            ]
        },
        '内存': {
            'objects': [
                {'keyword': 'database', 'x': 500, 'y': 200, 'scale': 5.0},
                {'keyword': 'check_mark', 'x': 1200, 'y': 250, 'scale': 2.5}
            ],
            'flows': [{'from': 0, 'to': 1, 'label': 'speed'}]
        },
        '单线程': {
            'objects': [
                {'keyword': 'gear', 'x': 600, 'y': 200, 'scale': 5.0},
                {'keyword': 'check_mark', 'x': 1200, 'y': 200, 'scale': 2.0}
            ],
            'flows': [{'from': 0, 'to': 1, 'label': 'no lock'}]
        },
        '数据结构': {
            'objects': [
                {'keyword': 'database', 'x': 300, 'y': 200, 'scale': 3.0},
                {'keyword': 'gear', 'x': 800, 'y': 250, 'scale': 3.5},
                {'keyword': 'database', 'x': 1300, 'y': 200, 'scale': 3.0}
            ],
            'flows': [
                {'from': 0, 'to': 1, 'label': '5 types'},
                {'from': 1, 'to': 2, 'label': 'optimized'}
            ]
        },
        '缓存流程': {
            'objects': [
                {'keyword': 'person_standing', 'x': 200, 'y': 200, 'scale': 3.0},
                {'keyword': 'laptop', 'x': 650, 'y': 250, 'scale': 3.5},
                {'keyword': 'database', 'x': 1100, 'y': 200, 'scale': 3.5},
                {'keyword': 'monitor', 'x': 1500, 'y': 250, 'scale': 2.5}
            ],
            'flows': [
                {'from': 0, 'to': 1, 'label': 'request'},
                {'from': 1, 'to': 2, 'label': 'check'},
                {'from': 2, 'to': 3, 'label': 'return'}
            ]
        },
        '命中': {
            'objects': [
                {'keyword': 'database', 'x': 500, 'y': 200, 'scale': 4.5},
                {'keyword': 'check_mark', 'x': 1100, 'y': 200, 'scale': 3.0}
            ],
            'flows': [{'from': 0, 'to': 1, 'label': 'HIT'}]
        },
        '穿透': {
            'objects': [
                {'keyword': 'person_standing', 'x': 300, 'y': 200, 'scale': 3.5},
                {'keyword': 'database', 'x': 850, 'y': 200, 'scale': 4.0},
                {'keyword': 'magnifying_glass', 'x': 1400, 'y': 250, 'scale': 2.5}
            ],
            'flows': [
                {'from': 0, 'to': 1, 'label': 'query'},
                {'from': 1, 'to': 2, 'label': 'miss'}
            ]
        },
        '雪崩': {
            'objects': [
                {'keyword': 'database', 'x': 400, 'y': 150, 'scale': 3.5},
                {'keyword': 'database', 'x': 900, 'y': 150, 'scale': 3.5},
                {'keyword': 'database', 'x': 1400, 'y': 150, 'scale': 3.5}
            ],
            'flows': [
                {'from': 0, 'to': 1, 'label': 'expire'},
                {'from': 1, 'to': 2, 'label': 'expire'}
            ]
        },
        '持久化': {
            'objects': [
                {'keyword': 'database', 'x': 400, 'y': 200, 'scale': 4.0},
                {'keyword': 'gear', 'x': 900, 'y': 280, 'scale': 2.5},
                {'keyword': 'database', 'x': 1400, 'y': 200, 'scale': 3.5}
            ],
            'flows': [
                {'from': 0, 'to': 1, 'label': 'RDB/AOF'},
                {'from': 1, 'to': 2, 'label': 'save'}
            ]
        },
        '应用': {
            'objects': [
                {'keyword': 'database', 'x': 400, 'y': 150, 'scale': 3.0},
                {'keyword': 'chat_bubble', 'x': 900, 'y': 200, 'scale': 3.0},
                {'keyword': 'gear', 'x': 1400, 'y': 250, 'scale': 3.0}
            ],
            'flows': [
                {'from': 0, 'to': 1, 'label': 'session'},
                {'from': 1, 'to': 2, 'label': 'queue'}
            ]
        },
        '总结': {
            'objects': [
                {'keyword': 'brain', 'x': 500, 'y': 180, 'scale': 4.0},
                {'keyword': 'check_mark', 'x': 1100, 'y': 200, 'scale': 3.0}
            ],
            'flows': [{'from': 0, 'to': 1, 'label': 'master'}]
        },
    }

    for key, value in scenes.items():
        if key in prompt:
            return json.dumps(value)

    return json.dumps({
        'objects': [{'keyword': 'database', 'x': 700, 'y': 250, 'scale': 4.0}],
        'flows': []
    })


from core.lineart_renderer import generate_lineart_video

script = [
    'Redis 是一个开源的内存数据结构存储系统',
    '它为什么这么快？因为内存存储加上单线程模型',
    '数据全部存在内存中，读写速度是磁盘的10万倍',
    '单线程避免了锁竞争，配合IO多路复用处理并发',
    '支持5种核心数据结构：String、Hash、List、Set、ZSet',
    '典型缓存流程：App请求先查Redis，命中直接返回',
    '缓存命中时响应时间在1毫秒以内',
    '缓存穿透：查询不存在的数据，请求直达数据库',
    '缓存雪崩：大量缓存同时过期，数据库瞬间压力暴增',
    'Redis提供RDB快照和AOF日志两种持久化方案',
    '应用场景包括：会话缓存、消息队列、排行榜、分布式锁',
    '掌握Redis是后端开发的必备技能',
]

print('生成 Redis 深度讲解视频...')
print('='*50)

output = generate_lineart_video(
    script,
    output_path='output/lineart_redis_deep.mp4',
    draw_duration=4.5,
    hold_duration=2.5,
    llm_fn=mock_llm,
)

print(f'视频已生成: {output}')
