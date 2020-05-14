# homeassistant-miio

支持小米空气净化器proH，可能也支持小米空气净化器3。

configuration.yaml内添加
```shell
    fan:
      - platform: xiaomi_airpurifierProH
        name: Bedroom Airpurifier
        host: xxx.xxx.xxx.xxx
        token: xxxxx
```
其实token貌似没有用到，所以不需要真实的token也行

支持小米wifi窗帘机

configuration.yaml内添加
```shell
    cover:
      - platform: xiaomi_cover
        name: Bedroom Curtain
        host: xxx.xxx.xxx.xxx
        token: xxxxx
```
