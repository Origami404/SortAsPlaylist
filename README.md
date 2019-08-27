## 简介
这是一个基于[NeteaseCloudAPI](https://github.com/Binaryify/NeteaseCloudMusicApi)的小工具, 用来对付没有跟网易云音乐联动的廉价辣鸡mp3
它可以把你网易云音乐里的歌**按歌单**放到文件夹里, 具体样式如下
```
00 - 歌单
    998 - 歌名 - 歌手
    999 - 歌名 - 歌手
01 - 歌单
    999 - 歌名 - 歌手
```
使用编号来把歌在mp3内按歌单顺序排序, 因为辣鸡mp3一般显示歌名都只显示前几个字符, 所以我把歌名放到歌手前面了, 不喜欢的可以在脚本里改

## 目前已知问题
- 当一个歌单很大, 网速很慢以至于在20min内下不完一个歌单的时候, 超过20min后下下来的歌会全都是0mb, 这时只要重启脚本就好了, 脚本会判断歌的大小来自动帮你重下
- 仅支持手机登陆, 帐号密码**明文**保存在`config.json`中, 请注意安全
- 为了能够方便地在歌单顶部添加/删除歌, 编号会从`(999-歌曲总数)`开始编, 但是这意味着如果你在歌单中间添加/删除了歌或者动了歌单顺序的话, 那就要重新下过所有歌了

## 使用
首先要安装[NeteaseCloudAPI](https://github.com/Binaryify/NeteaseCloudMusicApi)并使其运行.
```bash
git clong 
cd NeteaseCloudMusicApi
npm install
node app.js
```

然后编辑一下配置文件`config.json`就可以跑这个脚本了
```bash
git clone 
cd SortAsPlaylist
python -u main.py
```

配置项如下
```json
{
    "account": {
        "phone": "手机号",
        "password": "密码 !! 明文 注意安全 !!"
    },
    "filename": {
        // 要下载到的路径, 注意权限问题
        "music_root": "/mnt",
        // 你的文件系统不支持的字符以及要替换的字符
        // python的json.load()似乎有bug, 连续的转义字符如\\\"解析时会出错, 所以双引号只能变成单引号了
        "replace": [
            ["<", "＜"],
            [">", "＞"],
            [":", "："],
            ["/", "／"],
            ["\\", "-"],
            ["|", "｜"],
            ["?", "？"],
            ["*", "＊"],
            ["\"", "'"]
            
        ],
        // 歌名最大长度, 还未支持判断
        "max_length": 128
    },
    "api": {
        // api地址
        "url": "http://localhost:3000",
        // 是否缓存api结果
        "cache": false
    }
}
```