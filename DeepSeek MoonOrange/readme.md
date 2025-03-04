***DeepSeek MoonOrange***

**简介**

DeepSeek MoonOrange 是一个用于使用DeepSeek的api访问deepseek的界面程序。

本项目完全开源于https://github.com/Orangewang124/DeepSeek-MoonOrange

如果觉得有意思就帮我Star一下呗:)

**功能特性**

*功能 1：DeepSeek-V3* 默认模式

*功能 2：DeepSeek-R1* 选择深度思考时使用DeepSeek-R1模型，思考过程会展示在对话框

*功能 3：金鱼模式* 选择金鱼模式时deepseek将不记得之前的对话

*功能 4：记忆增强模式* 选择增强记忆模式时deepseek会回忆起他之前的思考过程

*功能 5：联网搜索*

点击联网搜索按钮即可使用联网搜索功能，选择左侧联网引擎即可更换联网引擎

默认Bing-Normal使用爬虫爬取Bing的搜索结果

注意：Bing-Normal搜索质量较差，很可能搜索不到结果，建议使用其他搜索引擎

其中Duck-General和Duck-News模式均使用DuckDuckGo引擎进行搜索，General是普通文本搜索,News是进行新闻类搜索，详情参考https://github.com/deedy5/duckduckgo_search

注意：DuckDuckGo引擎暂不支持中国网络环境，可能需要使用VPN

其中Tavily-General Tavily-News Tavily-Finance均使用tavily,引擎进行搜索，General是普通文本搜索,News是进行新闻类搜索，Finance是财经类搜索，详情参考https://app.tavily.com/playground

注意：Tavily引擎需要tavily的api，tavily官网https://tavily.com/ 可能需要使用VPN才能进入，注册账号的六位code需要Authenticator(ios系统)或 Ezi身份验证器(HarmonyOS Next系统)进行扫码获取

注意：目前Tavily支持一个账号一个月的1000次搜索api调用免费计划，详情参考tavily官网


*功能 6：上传文件*

点击上传文件后选择文件即可开始本地读取文件，这一行为完全在本地完成，且目前只支持读取文本类内容

一次最多上传5个文件，鼠标移到黑色deepseek图标上即可展示出文件的详细内容，包括文件名简写，文件类型和文件大小

注意：文件大小是实际的文件内容大小而非文件本身大小。请谨慎传输过大的文件，因为模型的上下文长度是有限制的，而在这一版代码中并未根据上下文长度限制而对文件大小做出相应限制，详情上下文长度限制请看https://api-docs.deepseek.com/zh-cn/quick_start/pricing

注意：并非所有的文件都支持读取（如图片类文件都不支持读取），目前仅支持各类可以直接读取的文本文件（如.txt .py）和.docx .pdf等

注意：当前对话中上传的文件内容并不会直接显示在当前对话框中，点击发送后当前对话只会显示上传的文件名，但文件内容将会放到历史记录中，加载历史记录后文件内容会显示在对话框中

注意：点击发送会将读取到的文件内容以对话的形式发给deepseek，请注意保护隐私信息


*功能 7：调节温度*

Temperature 参数默认为 1.0

DeepSeek官方建议如下，详情参考https://api-docs.deepseek.com/zh-cn/quick_start/parameter_settings

代码生成/数学解题 0.0

数据抽取/分析 1.0

通用对话/翻译 1.3

创意类写作/诗歌创作	1.5

**使用说明**

第一次打开时会自动创建chat_config.json文件，文件目录为DeepSeek MoonOrange.exe的同一级目录，格式如下

[
    {
        "api-key": "your-api-key",
        "theme_style": "litera",
        "tavily-api-key": "tavily-api-key"
    }
]

在提示窗口输入DeepSeek官方的api-key即可将your-api-key替换

如果需要更新api-key直接编辑chat_config.json即可

申请deepseek的api-key请查看https://api-docs.deepseek.com/

申请tavily的api-key请查看tavily官网https://tavily.com/

在输入框输入文字后点击发送或回车后即可调用deepseek的api与deepseek对话

在输入框若想换行请按Ctrl+Enter

点击程序左侧历史对话记录即可加载历史对话记录为当前对话

点击新建对话后可以开启新的对话

更换主题可以更改chat_config.json文件中"theme_style"对应值，默认为"litera"，其他主题请参考https://ttkbootstrap.readthedocs.io/en/latest/

请谨慎更改主题，避免程序无法运行，建议备份chat_config.json后再尝试

选择深度思考时使用DeepSeek-R1模型，思考过程会展示在对话框

选择金鱼模式时deepseek将不记得之前的对话

**其他说明**

历史记录文件为chat_history.json，文件目录为DeepSeek MoonOrange.exe的同一级目录，第一次使用会自动创建

如果程序有关于历史对话记录异常，建议检查历史对话记录文件是否为该格式，若格式不同请更改或删除历史对话记录文件后再重新运行本程序。

删除或更改历史对话记录文件可能会失去历史对话记录，建议先进行备份后再操作，请务必谨慎操作！！！

**版权声明**

该程序由MoonOrange及DeepSeek编写，只能用于非盈利目的。

图标及图片来源于DeepDeek官网和微博摸鱼阿八

*MoonOrange* 2025/03/03
