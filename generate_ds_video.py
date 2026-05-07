"""数据结构讲解视频 v4 — 横屏+小字字幕+中间文字+混合样式"""

import json
import os
import subprocess
import time
from pathlib import Path

# Disable proxy for TTS connections
for _k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"):
    os.environ.pop(_k, None)
os.environ["NO_PROXY"] = "*"

ROOT = Path(__file__).parent
OUTPUT_DIR = ROOT / "output" / "ds-video-v4"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FPS = 30
DURATION_MS = 120_000
VOICE = "zh-CN-YunxiNeural"

TOPICS = [
    {
        "name": "01_linear",
        "title": "线性表",
        # Graph A: 概览图 (根→两分支→四叶)
        "graph_a_nodes": [
            {"id": "n1", "label": "线性表", "role": "core"},
            {"id": "n2", "label": "顺序存储", "role": "storage"},
            {"id": "n3", "label": "链式存储", "role": "storage"},
            {"id": "n4", "label": "数组", "role": "processor"},
            {"id": "n5", "label": "连续内存", "role": "processor"},
            {"id": "n6", "label": "指针", "role": "result"},
            {"id": "n7", "label": "离散内存", "role": "result"},
        ],
        "graph_a_edges": [
            {"id": "e1", "from": "n1", "to": "n2", "label": "实现", "kind": "impl"},
            {"id": "e2", "from": "n1", "to": "n3", "label": "实现", "kind": "impl"},
            {"id": "e3", "from": "n2", "to": "n4", "label": "底层", "kind": "uses"},
            {"id": "e4", "from": "n2", "to": "n5", "label": "特性", "kind": "has"},
            {"id": "e5", "from": "n3", "to": "n6", "label": "底层", "kind": "uses"},
            {"id": "e6", "from": "n3", "to": "n7", "label": "特性", "kind": "has"},
        ],
        # Graph B: 对比图 (数组 vs 链表 并排)
        "graph_b_nodes": [
            {"id": "a1", "label": "数组[0]", "role": "storage"},
            {"id": "a2", "label": "数组[1]", "role": "storage"},
            {"id": "a3", "label": "数组[2]", "role": "storage"},
            {"id": "a4", "label": "数组[3]", "role": "storage"},
            {"id": "b1", "label": "节点A", "role": "processor"},
            {"id": "b2", "label": "节点B", "role": "processor"},
            {"id": "b3", "label": "节点C", "role": "processor"},
        ],
        "graph_b_edges": [
            {"id": "ae1", "from": "a1", "to": "a2", "label": "连续", "kind": "adjacent"},
            {"id": "ae2", "from": "a2", "to": "a3", "label": "连续", "kind": "adjacent"},
            {"id": "ae3", "from": "a3", "to": "a4", "label": "连续", "kind": "adjacent"},
            {"id": "be1", "from": "b1", "to": "b2", "label": "next", "kind": "points"},
            {"id": "be2", "from": "b2", "to": "b3", "label": "next", "kind": "points"},
        ],
        # Card pages content
        "cards_a_title": "顺序存储",
        "cards_a_items": ["内存连续分配", "按下标随机访问O(1)", "插入删除需移动元素O(N)", "适合频繁读取场景"],
        "cards_b_title": "链式存储",
        "cards_b_items": ["内存离散分配", "只能顺序访问O(N)", "插入删除只改指针O(1)", "适合频繁增删场景"],
        # Full explainer script (20 sentences)
        "explainer": [
            "线性表是最基础的数据结构，它把数据元素排成一条线性的序列。",
            "每个元素最多有一个前驱和一个后继，这就是典型的一对一关系。",
            "线性表有两种经典的实现方式，分别是顺序存储和链式存储。",
            "顺序存储的核心思想是用一段连续的内存空间来存放数据元素。",
            "本质上它就是一个数组，每个元素在内存中紧密相邻，中间没有空隙。",
            "因为内存是连续的，所以可以用下标直接定位到任意元素，随机访问非常快。",
            "时间复杂度是常数级别，也就是O(1)，这是顺序存储最大的优势。",
            "但它的缺点也很明显，插入和删除的时候需要移动大量元素。",
            "比如在数组中间插入一个元素，后面的所有元素都要往后移一位。",
            "链式存储的思路完全不同，它用指针把各个节点串联起来。",
            "每个节点包含两部分，一部分存数据，另一部分存下一个节点的地址。",
            "内存不需要连续分配，系统哪里有空闲就把节点存到哪里。",
            "插入和删除的时候，只需要修改指针的指向就行了，非常高效。",
            "但代价是无法像数组那样直接跳到第N个元素，必须从头逐个遍历。",
            "这就引出了一个重要的权衡，随机访问和插入删除效率之间的取舍。",
            "如果业务场景是读多写少，数组是更好的选择。",
            "如果需要频繁地插入和删除元素，链表会更合适。",
            "在实际开发中，很多高级数据结构都是基于线性表构建的。",
            "比如栈和队列可以用数组实现，也可以用链表实现。",
            "理解线性表的两种存储方式，是学习所有后续数据结构的基础。",
        ],
    },
    {
        "name": "02_linked",
        "title": "链表",
        "graph_a_nodes": [
            {"id": "n1", "label": "链表", "role": "core"},
            {"id": "n2", "label": "单链表", "role": "storage"},
            {"id": "n3", "label": "双链表", "role": "storage"},
            {"id": "n4", "label": "循环链表", "role": "storage"},
            {"id": "n5", "label": "head→A→B→NULL", "role": "result"},
            {"id": "n6", "label": "NULL←A⇄B→NULL", "role": "result"},
            {"id": "n7", "label": "A→B→C→A", "role": "result"},
        ],
        "graph_a_edges": [
            {"id": "e1", "from": "n1", "to": "n2", "label": "基本型", "kind": "type"},
            {"id": "e2", "from": "n1", "to": "n3", "label": "增强型", "kind": "type"},
            {"id": "e3", "from": "n1", "to": "n4", "label": "特殊型", "kind": "type"},
            {"id": "e4", "from": "n2", "to": "n5", "label": "结构", "kind": "shows"},
            {"id": "e5", "from": "n3", "to": "n6", "label": "结构", "kind": "shows"},
            {"id": "e6", "from": "n4", "to": "n7", "label": "结构", "kind": "shows"},
        ],
        "graph_b_nodes": [
            {"id": "h", "label": "head", "role": "pointer"},
            {"id": "a", "label": "A(data+next)", "role": "storage"},
            {"id": "b", "label": "B(data+next)", "role": "storage"},
            {"id": "c", "label": "C(data+next)", "role": "storage"},
            {"id": "null", "label": "NULL", "role": "result"},
        ],
        "graph_b_edges": [
            {"id": "e1", "from": "h", "to": "a", "label": "指向", "kind": "points"},
            {"id": "e2", "from": "a", "to": "b", "label": "next", "kind": "links"},
            {"id": "e3", "from": "b", "to": "c", "label": "next", "kind": "links"},
            {"id": "e4", "from": "c", "to": "null", "label": "尾部", "kind": "terminates"},
        ],
        "cards_a_title": "单链表详解",
        "cards_a_items": ["每个节点=数据域+指针域", "头指针指向第一个节点", "尾节点next指向NULL", "只能单向从头到尾遍历"],
        "cards_b_title": "链表面试题精选",
        "cards_b_items": ["反转链表: 三指针法", "检测环: 快慢指针法", "合并有序链表: 递归或迭代", "找中间节点: 快指针走两步"],
        "explainer": [
            "链表是最常用的动态数据结构之一，也是技术面试的高频考点。",
            "单链表是最基本的链表形式，每个节点由数据域和指针域两部分组成。",
            "数据域用来存储实际的业务数据，指针域存储下一个节点的内存地址。",
            "头指针是整个链表的入口，它指向链表的第一个节点。",
            "最后一个节点的指针域为空，用NULL表示链表到此结束。",
            "遍历单链表只能从头开始，沿着next指针逐个访问，不能跳转。",
            "双链表在单链表的基础上做了增强，每个节点多了一个前驱指针。",
            "这样不仅能向后遍历，还能向前遍历，操作更加灵活方便。",
            "代价是每个节点多占用一个指针的内存空间，并且插入删除时要维护两个指针。",
            "循环链表是一种特殊的链表，最后一个节点不再指向空。",
            "它指向头节点，形成一个环形结构，从任意节点出发都能遍历整个链表。",
            "循环链表常用于实现约瑟夫环问题和操作系统的轮转调度算法。",
            "链表最大的优势在于插入和删除操作，只需要修改指针指向即可。",
            "不需要像数组那样移动大量元素，时间复杂度是常数级别的。",
            "但链表的缺点是失去了随机访问能力，查找第N个元素需要O(N)时间。",
            "面试中经常考察的链表操作包括反转、合并、检测环和找中间节点。",
            "反转链表的经典方法是三指针法，用prev、curr、next三个指针协作。",
            "检测链表是否有环可以用快慢指针法，快指针走两步，慢指针走一步。",
            "如果链表有环，两个指针一定会在某个节点相遇。",
            "掌握链表的关键是理解指针操作和边界条件，多画图多练习。",
        ],
    },
    {
        "name": "03_stack_queue",
        "title": "栈和队列",
        "graph_a_nodes": [
            {"id": "n1", "label": "受限线性表", "role": "core"},
            {"id": "n2", "label": "栈", "role": "storage"},
            {"id": "n3", "label": "队列", "role": "storage"},
            {"id": "n4", "label": "LIFO后进先出", "role": "rule"},
            {"id": "n5", "label": "FIFO先进先出", "role": "rule"},
            {"id": "n6", "label": "push/pop", "role": "input"},
            {"id": "n7", "label": "enqueue/dequeue", "role": "output"},
        ],
        "graph_a_edges": [
            {"id": "e1", "from": "n1", "to": "n2", "label": "约束", "kind": "constrains"},
            {"id": "e2", "from": "n1", "to": "n3", "label": "约束", "kind": "constrains"},
            {"id": "e3", "from": "n2", "to": "n4", "label": "规则", "kind": "follows"},
            {"id": "e4", "from": "n3", "to": "n5", "label": "规则", "kind": "follows"},
            {"id": "e5", "from": "n6", "to": "n2", "label": "操作", "kind": "operates"},
            {"id": "e6", "from": "n3", "to": "n7", "label": "操作", "kind": "operates"},
        ],
        "graph_b_nodes": [
            {"id": "s1", "label": "栈底", "role": "storage"},
            {"id": "s2", "label": "元素A", "role": "processor"},
            {"id": "s3", "label": "元素B", "role": "processor"},
            {"id": "s4", "label": "栈顶", "role": "input"},
            {"id": "q1", "label": "队头出", "role": "output"},
            {"id": "q2", "label": "元素X", "role": "processor"},
            {"id": "q3", "label": "元素Y", "role": "processor"},
            {"id": "q4", "label": "队尾入", "role": "input"},
        ],
        "graph_b_edges": [
            {"id": "se1", "from": "s1", "to": "s2", "label": "压入", "kind": "push"},
            {"id": "se2", "from": "s2", "to": "s3", "label": "压入", "kind": "push"},
            {"id": "se3", "from": "s3", "to": "s4", "label": "栈顶", "kind": "top"},
            {"id": "qe1", "from": "q4", "to": "q3", "label": "入队", "kind": "enqueue"},
            {"id": "qe2", "from": "q3", "to": "q2", "label": "传递", "kind": "passes"},
            {"id": "qe3", "from": "q2", "to": "q1", "label": "出队", "kind": "dequeue"},
        ],
        "cards_a_title": "栈的典型应用",
        "cards_a_items": ["函数调用栈管理执行上下文", "表达式求值: 中缀转后缀", "括号匹配: 遇到左括号压栈", "浏览器前进后退功能"],
        "cards_b_title": "队列的典型应用",
        "cards_b_items": ["任务调度: 操作系统进程队列", "消息队列: 异步处理解耦", "广度优先搜索BFS", "打印任务排队管理"],
        "explainer": [
            "栈和队列都是操作受限的线性表，它们限制了插入和删除的位置。",
            "栈只能在同一端进行插入和删除，这一端叫做栈顶。",
            "往栈里放元素叫做压栈，也叫入栈，对应的操作是push。",
            "从栈里取元素叫做出栈，也叫弹栈，对应的操作是pop。",
            "栈遵循后进先出的原则，英文缩写是LIFO。",
            "最后放进去的元素最先被取出来，就像一摞盘子只能从最上面取。",
            "栈在计算机科学中有着极其广泛的应用。",
            "最典型的就是函数调用栈，每次调用函数都会在栈顶压入一个栈帧。",
            "函数返回时栈帧弹出，恢复之前的执行上下文。",
            "表达式求值也依赖栈，中缀表达式转后缀表达式就用到了栈。",
            "括号匹配是栈的经典应用，遇到左括号压栈，遇到右括号弹栈匹配。",
            "队列的操作方式和栈完全不同，它从一端进，从另一端出。",
            "从队尾放入元素叫做入队，用enqueue操作。",
            "从队头取出元素叫做出队，用dequeue操作。",
            "队列遵循先进先出的原则，英文缩写是FIFO。",
            "最先放入的元素最先被取出，就像排队买票一样先到先得。",
            "操作系统用队列来管理进程调度，按照先来后到的顺序执行。",
            "消息队列是分布式系统的核心组件，实现了服务之间的异步解耦。",
            "广度优先搜索算法BFS也是基于队列实现的，按层遍历图或树。",
            "还有一种特殊的数据结构叫双端队列，两端都可以进行插入和删除。",
        ],
    },
    {
        "name": "04_tree",
        "title": "二叉树",
        "graph_a_nodes": [
            {"id": "n1", "label": "根节点", "role": "core"},
            {"id": "n2", "label": "左子树", "role": "storage"},
            {"id": "n3", "label": "右子树", "role": "storage"},
            {"id": "n4", "label": "BST", "role": "processor"},
            {"id": "n5", "label": "堆", "role": "processor"},
            {"id": "n6", "label": "叶子", "role": "result"},
            {"id": "n7", "label": "叶子", "role": "result"},
            {"id": "n8", "label": "叶子", "role": "result"},
            {"id": "n9", "label": "叶子", "role": "result"},
        ],
        "graph_a_edges": [
            {"id": "e1", "from": "n1", "to": "n2", "label": "左孩子", "kind": "child"},
            {"id": "e2", "from": "n1", "to": "n3", "label": "右孩子", "kind": "child"},
            {"id": "e3", "from": "n2", "to": "n4", "label": "变体", "kind": "variant"},
            {"id": "e4", "from": "n3", "to": "n5", "label": "变体", "kind": "variant"},
            {"id": "e5", "from": "n2", "to": "n6", "label": "左", "kind": "child"},
            {"id": "e6", "from": "n2", "to": "n7", "label": "右", "kind": "child"},
            {"id": "e7", "from": "n3", "to": "n8", "label": "左", "kind": "child"},
            {"id": "e8", "from": "n3", "to": "n9", "label": "右", "kind": "child"},
        ],
        "graph_b_nodes": [
            {"id": "r", "label": "50", "role": "core"},
            {"id": "l1", "label": "30", "role": "storage"},
            {"id": "r1", "label": "70", "role": "storage"},
            {"id": "l2", "label": "20", "role": "processor"},
            {"id": "l3", "label": "40", "role": "processor"},
            {"id": "r2", "label": "60", "role": "processor"},
            {"id": "r3", "label": "80", "role": "processor"},
        ],
        "graph_b_edges": [
            {"id": "e1", "from": "r", "to": "l1", "label": "<50", "kind": "left"},
            {"id": "e2", "from": "r", "to": "r1", "label": ">50", "kind": "right"},
            {"id": "e3", "from": "l1", "to": "l2", "label": "<30", "kind": "left"},
            {"id": "e4", "from": "l1", "to": "l3", "label": ">30", "kind": "right"},
            {"id": "e5", "from": "r1", "to": "r2", "label": "<70", "kind": "left"},
            {"id": "e6", "from": "r1", "to": "r3", "label": ">70", "kind": "right"},
        ],
        "cards_a_title": "二叉搜索树BST",
        "cards_a_items": ["左子树所有值 < 根节点", "右子树所有值 > 根节点", "查找时间复杂度 O(log N)", "中序遍历得到有序序列"],
        "cards_b_title": "二叉树遍历方式",
        "cards_b_items": ["前序: 根→左→右", "中序: 左→根→右", "后序: 左→右→根", "层序: 用队列按层遍历"],
        "explainer": [
            "二叉树是一种非常重要的非线性数据结构，它的每个节点最多有两个子节点。",
            "这两个子节点分别叫做左孩子和右孩子，这是二叉树的基本定义。",
            "没有子节点的节点叫做叶子节点，就像大树最末端的叶子。",
            "二叉搜索树是最常用的二叉树变体，它有一个重要的排序性质。",
            "左子树中所有节点的值都小于根节点，右子树中所有节点的值都大于根节点。",
            "这个性质让查找操作变得非常高效，每次比较都能排除一半的数据。",
            "查找的时间复杂度是O(log N)，在百万数据中最多比较20次就能找到。",
            "堆是另一种重要的二叉树变体，它是一棵完全二叉树。",
            "最大堆的父节点总是大于等于子节点，堆顶是最大值。",
            "最小堆则相反，父节点总是小于等于子节点，堆顶是最小值。",
            "堆常用于实现优先队列，也是一堆排序算法的核心数据结构。",
            "二叉树有三种基本的遍历方式，分别是前序、中序和后序遍历。",
            "前序遍历的顺序是根左右，先访问根节点再遍历左右子树。",
            "中序遍历的顺序是左根右，对于BST来说会得到有序序列。",
            "后序遍历的顺序是左右根，常用于释放树的内存空间。",
            "还有一种层序遍历，用队列按层从上到下、从左到右依次访问。",
            "二叉树是数据库索引B+树的基础，理解二叉树就理解了索引的原理。",
            "文件系统的目录结构、编译器的语法分析树都是树结构的应用。",
            "理解递归是掌握二叉树的关键，因为树的定义本身就是递归的。",
            "很多复杂的算法问题都可以用分治思想加二叉树递归来优雅地解决。",
        ],
    },
    {
        "name": "05_graph",
        "title": "图",
        "graph_a_nodes": [
            {"id": "n1", "label": "图", "role": "core"},
            {"id": "n2", "label": "顶点", "role": "storage"},
            {"id": "n3", "label": "边", "role": "storage"},
            {"id": "n4", "label": "有向图", "role": "processor"},
            {"id": "n5", "label": "无向图", "role": "processor"},
            {"id": "n6", "label": "邻接矩阵", "role": "result"},
            {"id": "n7", "label": "邻接表", "role": "result"},
        ],
        "graph_a_edges": [
            {"id": "e1", "from": "n1", "to": "n2", "label": "组成", "kind": "contains"},
            {"id": "e2", "from": "n1", "to": "n3", "label": "组成", "kind": "contains"},
            {"id": "e3", "from": "n1", "to": "n4", "label": "分类", "kind": "type"},
            {"id": "e4", "from": "n1", "to": "n5", "label": "分类", "kind": "type"},
            {"id": "e5", "from": "n2", "to": "n6", "label": "存储", "kind": "stored"},
            {"id": "e6", "from": "n2", "to": "n7", "label": "存储", "kind": "stored"},
        ],
        "graph_b_nodes": [
            {"id": "a", "label": "城市A", "role": "storage"},
            {"id": "b", "label": "城市B", "role": "storage"},
            {"id": "c", "label": "城市C", "role": "storage"},
            {"id": "d", "label": "城市D", "role": "storage"},
            {"id": "e", "label": "城市E", "role": "processor"},
        ],
        "graph_b_edges": [
            {"id": "e1", "from": "a", "to": "b", "label": "100km", "kind": "road"},
            {"id": "e2", "from": "a", "to": "c", "label": "200km", "kind": "road"},
            {"id": "e3", "from": "b", "to": "d", "label": "150km", "kind": "road"},
            {"id": "e4", "from": "c", "to": "d", "label": "80km", "kind": "road"},
            {"id": "e5", "from": "d", "to": "e", "label": "120km", "kind": "road"},
            {"id": "e6", "from": "b", "to": "e", "label": "300km", "kind": "road"},
        ],
        "cards_a_title": "图的遍历算法",
        "cards_a_items": ["BFS广搜: 队列层层扩展", "DFS深搜: 递归深度探索", "BFS求最短路径(无权图)", "DFS检测环和连通分量"],
        "cards_b_title": "图的经典应用",
        "cards_b_items": ["Dijkstra最短路径算法", "社交网络好友推荐", "网页排名PageRank算法", "地图导航路径规划"],
        "explainer": [
            "图是最通用的数据结构，它能表示现实世界中任意的多对多关系。",
            "图由两个基本元素组成，顶点代表实体，边代表实体之间的关系。",
            "如果边有方向，就是有向图，比如微博的关注关系我关注你不代表你关注我。",
            "如果边没有方向，就是无向图，比如微信好友关系是双向的。",
            "图有两种主要的存储方式，邻接矩阵和邻接表。",
            "邻接矩阵用二维数组表示顶点之间的关系，查询两点是否相连非常快。",
            "但空间复杂度是O(N平方)，对于稀疏图会浪费大量内存。",
            "邻接表用链表存储每个顶点的邻居节点，空间更节省。",
            "对于稀疏图来说，邻接表是更好的选择。",
            "图的遍历有两种基本方式，广度优先搜索和深度优先搜索。",
            "广度优先搜索BFS用队列实现，像水波一样从起点一层层向外扩展。",
            "BFS能保证找到无权图中的最短路径，因为它总是先访问离起点近的节点。",
            "深度优先搜索DFS用栈或递归实现，沿着一条路走到底再回溯。",
            "DFS常用于检测图中是否存在环，以及求连通分量。",
            "带权图的边带有权重值，可以表示距离、时间或费用等实际意义。",
            "Dijkstra算法是求解单源最短路径的经典算法，适用于非负权图。",
            "它的核心思想是贪心策略，每次选择距离最近的未访问节点进行扩展。",
            "图论在实际应用中无处不在，社交网络、地图导航、推荐系统都依赖图。",
            "谷歌的PageRank算法本质上就是在互联网这张大图上做随机游走。",
            "掌握图论的基本概念和算法，是成为优秀工程师的必备技能。",
        ],
    },
]


def ensure_bundle():
    build_dir = ROOT / "remotion-renderer" / "build"
    if build_dir.exists() and any(build_dir.iterdir()):
        print("[OK] Bundle exists")
        return
    print("[...] Building bundle...")
    subprocess.run(["npx", "remotion", "bundle"], cwd=ROOT / "remotion-renderer", check=True)


def build_layout(topic: dict) -> Path:
    """Build layout JSON: landscape, small subtitles, centered text in empty scenes."""
    from engine.bridge.graph_pipeline import (
        _normalize_audio_tracks,
        _generate_explainer_audio_tracks,
        apply_graph_layout,
        build_default_plan,
        classify_graph,
        FPS,
    )

    name = topic["name"]
    out_dir = OUTPUT_DIR / name
    out_dir.mkdir(parents=True, exist_ok=True)
    layout_path = out_dir / "layout.json"
    if layout_path.exists():
        print(f"  [SKIP]")
        return layout_path

    # ── 1. Generate TTS: intro + 20-sentence script ──
    intro_text = "我是武汉科技大学的韩智轩"
    print(f"  [1/5] TTS intro + {len(topic['explainer'])} sentences...")
    intro_tracks = _generate_explainer_audio_tracks(
        [intro_text], total_ms=DURATION_MS, voice=VOICE, rate=0,
    )
    main_tracks = _generate_explainer_audio_tracks(
        topic["explainer"], total_ms=DURATION_MS, voice=VOICE, rate=0,
    )
    main_tracks = _normalize_audio_tracks(main_tracks)

    # Intro duration from actual audio
    intro_dur = intro_tracks[0]["duration"] if intro_tracks else 120

    # Shift main tracks to start after intro
    for t in main_tracks:
        t["start"] += intro_dur
    # Fix duplicate IDs between intro and main tracks
    for t in main_tracks:
        t["id"] = f"main_{t['id']}"
    audio_tracks = intro_tracks + main_tracks

    audio_end = max((t["start"] + t["duration"] for t in audio_tracks), default=0)
    total_frames = max(3600, audio_end)

    # ── 2. Build subtitle elements (small text at bottom) ──
    elements = []
    for track in audio_tracks:
        elements.append({
            "id": f"sub_{track['id']}",
            "type": "text",
            "text": track["text"],
            "x": 960, "y": 960,
            "fontSize": 28,
            "color": "#f8fbff",
            "fontWeight": 600,
            "textAlign": "center",
            "lineHeight": 1.35,
            "maxWidth": 1200,
            "start": track["start"],
            "duration": track["duration"],
            "zIndex": 20,
            "animation": {"enter": "blur-in", "exit": "fade", "duration": 8},
        })

    # ── 3. Build two graphs with positions (landscape) ──
    width, height = 1920, 1080
    dsl_a = {
        "title": "",  # no big text
        "summary": "",
        "nodes": topic["graph_a_nodes"],
        "edges": topic["graph_a_edges"],
        "steps": [],
        "timeline": [],
    }
    graph_a = apply_graph_layout(dsl_a, width=width, height=height)
    graph_a["title"] = ""
    graph_a["summary"] = ""

    dsl_b = {
        "title": "",
        "summary": "",
        "nodes": topic["graph_b_nodes"],
        "edges": topic["graph_b_edges"],
        "steps": [],
        "timeline": [],
    }
    graph_b = apply_graph_layout(dsl_b, width=width, height=height)
    graph_b["title"] = ""
    graph_b["summary"] = ""

    # ── 4. Add animation plans ──
    for g in [graph_a, graph_b]:
        plan = build_default_plan(g, total_frames, audio_tracks)
        # Clear ALL text in animation plan (steps and shots)
        for step in plan.get("steps", []):
            step.pop("text", None)
        for shot in plan.get("shots", []):
            shot.pop("text", None)
        g["animation_plan"] = plan
        g["shots"] = plan.get("shots", [])
        g["timeline"] = []
        g["steps"] = []

    # ── 5. Build scene sequence: intro → hook → graphA → cardsA → graphB → cardsB ──

    # Divide main audio (excluding intro) into 5 segments
    main_audio = [t for t in audio_tracks if t["start"] >= intro_dur]
    n = len(main_audio)
    seg_size = n // 5
    segments = []
    for i in range(5):
        start_idx = i * seg_size
        end_idx = (i + 1) * seg_size if i < 4 else n
        seg_tracks = main_audio[start_idx:end_idx]
        if seg_tracks:
            seg_start = seg_tracks[0]["start"]
            seg_end = seg_tracks[-1]["start"] + seg_tracks[-1]["duration"]
            segments.append({"start": seg_start, "duration": seg_end - seg_start, "tracks": seg_tracks})

    scenes = []

    # Intro scene — self introduction with voice-over
    scenes.append({
        "id": "scene_intro",
        "type": "hook",
        "start": 0,
        "duration": intro_dur,
        "text": "我是武汉科技大学的韩智轩",
    })

    scene_types = ["hook", "graph_a", "cards_a", "graph_b", "cards_b"]
    for i, (stype, seg) in enumerate(zip(scene_types, segments)):
        scene = {
            "id": f"scene_{stype}",
            "type": "graph" if "graph" in stype else stype.split("_")[0],
            "start": seg["start"],
            "duration": seg["duration"],
        }
        if stype == "hook":
            scene["type"] = "hook"
            scene["text"] = topic["title"]
        elif stype == "graph_a":
            scene["type"] = "graph"
            scene["graph"] = graph_a
        elif stype == "cards_a":
            scene["type"] = "cards"
            scene["title"] = topic["cards_a_title"]
            scene["items"] = topic["cards_a_items"]
        elif stype == "graph_b":
            scene["type"] = "graph"
            scene["graph"] = graph_b
        elif stype == "cards_b":
            scene["type"] = "cards"
            scene["title"] = topic["cards_b_title"]
            scene["items"] = topic["cards_b_items"]
        scenes.append(scene)

    # Crossfade overlaps
    for i in range(len(scenes) - 1):
        overlap = 8
        scenes[i]["overlapOut"] = overlap
        scenes[i + 1]["overlapIn"] = overlap

    # ── 6. Assemble layout ──
    layout = {
        "width": width,
        "height": height,
        "fps": FPS,
        "durationInFrames": total_frames,
        "background": "#070b10",
        "scene_type": "graph",
        "graph": graph_a,  # fallback graph
        "nodes": graph_a["nodes"],
        "edges": graph_a["edges"],
        "elements": elements,  # small subtitles only
        "shots": [],
        "scenes": scenes,
        "audioTracks": audio_tracks,
        "explainerScript": topic["explainer"],
    }

    with open(layout_path, "w", encoding="utf-8") as f:
        json.dump(layout, f, ensure_ascii=False, indent=2)

    with open(out_dir / "script.txt", "w", encoding="utf-8") as f:
        for line in topic["explainer"]:
            f.write(line + "\n")

    cov = audio_end / total_frames * 100
    print(f"  [OK] {len(audio_tracks)} tracks, {total_frames} frames, coverage={cov:.0f}%")
    return layout_path


def render_video(topic: dict, layout_path: Path) -> Path:
    name = topic["name"]
    video_path = OUTPUT_DIR / f"{name}.mp4"
    if video_path.exists():
        print(f"  [SKIP]")
        return video_path

    print(f"  Rendering...")
    t0 = time.time()
    abs_l = str(layout_path.resolve()).replace("\\", "/")
    abs_o = str(video_path.resolve()).replace("\\", "/")
    r = subprocess.run(
        ["node", "render-agent-semantic.mjs", abs_l, abs_o],
        cwd=ROOT / "remotion-renderer",
        capture_output=True, text=True, encoding="utf-8",
    )
    if r.returncode != 0:
        print(f"  [ERR] {r.stderr[-300:] if r.stderr else '?'}")
        raise RuntimeError(f"Render failed: {name}")
    print(f"  [OK] {video_path.name} ({time.time()-t0:.0f}s)")
    return video_path


def concat_and_sub(videos, topics):
    final = OUTPUT_DIR / "data_structures_final.mp4"
    concat_list = OUTPUT_DIR / "concat.txt"
    with open(concat_list, "w") as f:
        for v in videos:
            f.write(f"file '{v.as_posix()}'\n")
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list), "-c", "copy", str(final)],
        capture_output=True, text=True, encoding="utf-8",
    )
    print(f"[OK] Final: {final.name} ({final.stat().st_size / 1024 / 1024:.1f} MB)")


def _fmt(ms):
    h, r = divmod(ms, 3600000)
    m, r = divmod(r, 60000)
    s, ml = divmod(r, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ml:03d}"


def main():
    print("=" * 60)
    print("  数据结构讲解 v4 — 横屏+小字字幕+中间文字")
    print("=" * 60)
    t0 = time.time()
    ensure_bundle()

    print(f"\n{'='*60}\n  Layouts\n{'='*60}")
    layouts = []
    for t in TOPICS:
        print(f"\n--- {t['name']} ---")
        layouts.append(build_layout(t))

    print(f"\n{'='*60}\n  Render\n{'='*60}")
    videos = []
    for t, lp in zip(TOPICS, layouts):
        print(f"\n--- {t['name']} ---")
        videos.append(render_video(t, lp))

    concat_and_sub(videos, TOPICS)
    print(f"\n  DONE! {(time.time()-t0)/60:.1f} min")
    print(f"  {OUTPUT_DIR / 'data_structures_final.mp4'}")


if __name__ == "__main__":
    main()
