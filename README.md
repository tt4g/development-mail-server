[docker-mailserver][docker-mailserver GitHub]
使用してローカル配送しかしない（外部への配送を行わない）メールサーバーを Docker コンテナ内に
作成する。

## メールサーバー

### 構成

[docker-mailserver][docker-mailserver GitHub] の Docker コンテナ内で起動している
`postfix` で SMTP プロトコルを処理し `dovecot` で POP3/IMAP プロトコルを処理する。

[development-mail-server.env](./development-mail-server.env) で環境変数
`ENABLE_POSTFIX_VIRTUAL_TRANSPORT=1` が定義されているため、 バーチャルドメインが有効に
なっている。

[development-mail-server.env](./development-mail-server.env) の機能によって
`setup email add` コマンドで追加されたメールアドレスに対して `dovecot` が管理する
メールボックスが生成されるようになっている。
バーチャルドメインとメールボックスの関連も `virtual_mailbox_maps` が参照するファイルにも
自動的に追記される。
さらに、 `virtual_mailbox_domains` にすべてのバーチャルドメインが列挙される。
環境変数 `POSTFIX_DAGENT=lmtp:unix:/var/run/dovecot/lmtp` の設定によって
`postfix` は `virtual_mailbox_maps` で定義されているバーチャルドメイン宛のメールを
`dovecot` の LMTP サーバーに渡して `dovecot` が管理するメールボックスに配送する。

Docker コンテナ内から配送する際には
[docker-data/mail-server/config/postfix-transport_maps](./docker-data/mail-server/config/postfix-transport_maps)
に記載されているトランスポート設定によって、メールドメイン
`development-virtual.example.com` 以外のメールドメインが宛先になっているメールは
全て Docker コンテナ内のローカル配送になる。

宛先不明のローカル配送メールは
[docker-data/mail-server/config/postfix-main.cf](./docker-data/mail-server/config/postfix-main.cf)
の `luser_relay = catchall` 設定によって `catchall` アカウントに配送される。

**TIP:** `development-virtual.example.com` はローカル配送にならないため、
バーチャルドメインのトランスポートマップで配送先が解決される。
バーチャルドメインにアカウントが存在しない場合は宛先不明で配送に失敗する。

ローカル開発中は `development-virtual.example.com` をメールドメインとする
メールアカウントを追加することで、 Docker コンテナ内のメールサーバーに対する SMTP/POP3
プロトコルによるメール交換が実現できる。

### 作成済みアカウント

- `catchall@development-mail-server.example.com`

    Docker コンテナ内のローカルユーザーのアカウント。
    他のローカルアカウントに配送されなかったメールの配送先メールアカウント。
    パスワードは `catchall` が設定されている。

- `foo@development-virtual.example.com`

    バーチャルドメインで定義されているメールアカウント。
    パスワードは `foo` が設定されている。

- `bar@development-virtual.example.com`

    バーチャルドメインで定義されているメールアカウント。
    パスワードは `foo` が設定されている。

- `baz@development-virtual.example.com`

    バーチャルドメインで定義されているメールアカウント。
    パスワードは `foo` が設定されている。

### 注意

#### 初期メールアカウント

環境変数 `ENABLE_LDAP` が `1` で有効になっていない限り、
[docker-mailserver][docker-mailserver GitHub] の仕様で
[docker-data/mail-server/config/postfix-accounts.cf](./docker-data/mail-server/config/postfix-accounts.cf)
に最低１つはメールアカウントが存在しないとメールサーバーが起動に失敗する。

See: https://github.com/docker-mailserver/docker-mailserver/tree/v10.5.0#starting-for-the-first-time

`postfix-accounts.cf` に記載するメールアカウント情報は
`./setup.sh [-Z] email add <user@domain> [<password>]` で作成する方法と、
https://docker-mailserver.github.io/docker-mailserver/v10.5/config/user-management/accounts/
で紹介されている Docker コンテナを一時的に起動して作成する方法がある。

```shell
$ docker run --rm \
  -e MAIL_USER=user1@example.com \
  -e MAIL_PASS=mypassword \
  -it mailserver/docker-mailserver:10.5.0 \
  /bin/sh -c 'echo "$MAIL_USER|$(doveadm pw -s SHA512-CRYPT -u $MAIL_USER -p $MAIL_PASS)"' >> postfix-accounts.cf
```

`setup.sh` も Docker コンテナ内の `setup` コマンドを呼び出ししているだけなので、
Docker コンテナ起動後であれば `setup email add <user@domain> [<password>]` で
メールアカウントをコンテナ内からも追加できる。

#### SMTP のみのサーバ―を構築する

環境変数 `SMTP_ONLY` が `1` になっていると
[docker-mailserver][docker-mailserver GitHub] は SMTP daemon のみを起動する。

`ENABLE_POP3=1` で POP3 を有効化するために、このリポジトリでは `SMTP_ONLY` を
定義していない (See: [development-mail-server.env](./development-mail-server.env))。

#### Windows 環境で正常に動作しない

Docker For Windows などの環境では `docker-compose logs development-mail-server` を
実行すると次のようなエラーメッセージが出力され続けている事がある。

```
development-mail-server    | Apr  8 14:02:34 development-mail-server dovecot: master: Fatal: Failed to start listeners
development-mail-server    | Apr  8 14:02:34 development-mail-server dovecot: master: Error: bind(/var/spool/postfix/private/auth) failed: Input/output error
development-mail-server    | Apr  8 14:02:34 development-mail-server dovecot: master: Error: service(auth): net_listen_unix(/var/spool/postfix/private/auth) failed: Input/output error
```

これは `/var/spool/postfix/private/auth` にソケットを生成できないために発生しているエラー。
Docker For Windows ではボリュームとしてマウントしたディレクトリでソケット生成に失敗する様子。

[docker-compose.yml](./docker-compose.yml) で該当ディレクトリをマウントしている箇所を
コメントアウトして起動できるようにする。

**TIP:** `/var/spool/postfix` が `/var/mail-state/spool-postfix` へのシンボリックリンク。

```diff
     volumes:
       - type: bind
         source: ./docker-data/mail-server/mail-data/
         target: /var/mail/
         # Windows 環境では `/var/mail-state/` のマウントはコメントアウトする。
-      - type: bind
-        source: ./docker-data/mail-server/mail-state/
-        target: /var/mail-state/
+#      - type: bind
+#        source: ./docker-data/mail-server/mail-state/
+#        target: /var/mail-state/
```

## メール送受信スクリプト

Requirements Python 3.7+

### Setup

```bash
$ python -m venv venv
$ . venv/Scripts/activate
$ python -m pip install pip-tools
$ pip-sync requirements.txt requirements-dev.txt
```

### send_email.py

[scripts/send_email.py](./scripts/send_email.py) で SMTP プロトコルでメールを配信できる。

```shell
$ python scripts/send_email.py
```

### pop_email.py

[scripts/pop_email.py](./scripts/pop_email.py) で POP プロトコルでメールを受信できる。

```shell
$ python scripts/pop_email.py
```

[docker-mailserver GitHub]:https://github.com/docker-mailserver/docker-mailserver
