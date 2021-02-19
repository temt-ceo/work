# work
This is the repository my AI work sits inside.

## AI開発ソースコード
https://www.kaggle.com/takashitahara/stock-expected-move-analysis

## 環境構築（Mac）
```
# brew install
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"

# PATH configure
cd ~
echo 'eval $(/opt/homebrew/bin/brew shellenv)' >> /Users/taharatakashi/.zprofile

# Install Python3
brew install python

# Apache configure
which httpd
which apachectl
sudo vi /etc/apache2/httpd.conf

## DocumentRootをProject Pathに変更
DocumentRoot "/Users/Path_To_Project_Files/public_html/"
ScriptAliasMatch ^/cgi-bin/((?!(?i:webobjects)).*$) "/Users/taharatakashi/AI/work/public_html/cgi-bin/$1"

## .htaccessを使用可能にする
<Directory >
　　　　AllowOverride All

＃# cgiの設定
mod_cgi.so, mod_userdir.so, mod_rewrite.soのコメントを外す

## AddHandler cgi~script .cgi をコメントを外し .pyを足す
Options FollowSymLinks Multiviews に ExecCGIを足す

## ApacheのUserを変更し、/Users/UserName/以下のファイルへアクセス可能にする
User _www => User (自らのUserName)

### error_log初期化
sudo bash -c 'echo > /var/log/apache2/error_log'
sudo /usr/sbin/apachectl restart

# Git clone
git clone https://github.com/temt-ceo/work.git
chmod 755 public_html

# Start Apache
sudo /usr/sbin/apachectl start

# flask インストール(リモートサーバと共通コマンド)
python3 -m pip install --upgrade pip --user
python3 -m pip install Flask --user
python3 -m pip install sklearn --user
python3 -m pip install pandas --user

# index.pyに以下の記述を追加
import site
site.addsitedir('/Users/taharatakashi/Library/Python/3.9/lib/python/site-packages')


# localhost確認

# git push
git push origin HEAD:main


## macOS Big Sur(Apple M1チップ)への対応
1. ターミナルを複製し名前をターミナル x86にリネーム。rosettaを有効にする。
2. Mac再起動し、ターミナル x86を起動
3. archをコマンドし'i386'が表示されrosetta上でターミナルが起動していることを確認する
4. pip3 install sklearn でsklearnをインストールする
5. python3 -m pip install pandas --user がpep517でビルドできないエラーを吐いた場合
  5-1. pip3 install Cython
  5-2. `pip3 install numpy --no-use-pep517` もしくは
       `python3 -m pip install --no-binary :all: --no-use-pep517 numpy==1.20rc1`
       これでi386環境でpep517を使用せずにwheelでnumpyをビルド・インストールできる
       しかしどちらの方法も、エラーの内容は違うがその後の
       `python3 -m pip install pandas --user`コマンドでnumpyに問題があるのでインストールできないと言われる..
       ✴️`--no-cache`をつけないとダウンロードしないで保存されているバイナリでインストールしようとするので気をつけること。
  5-3. file $(which python)と打つ
       `
        /usr/bin/python: Mach-O universal binary with 2 architectures: [x86_64:Mach-O 64-bit executable x86_64] [arm64e:Mach-O 64-bit executable arm64e]
        /usr/bin/python (for architecture x86_64):	Mach-O 64-bit executable x86_64
        /usr/bin/python (for architecture arm64e):	Mach-O 64-bit executable arm64e
       `
       と表示されルことを確認
  5-4. brew install miniforge
       https://towardsdatascience.com/tensorflow-2-4-on-apple-silicon-m1-installation-under-conda-environment-ba6de962b3b8
       を参考にinstallする
         => 結果はダメ（原因はBy installing the apple silicon version of numpy, packages broke with wrong arch error.ということ.）
  5-5. numpy-1.20.0-cp39-cp39-macosx_11_0_arm64.whl (cacheされたnumpy)
       numpy-1.20.0rc1


```
