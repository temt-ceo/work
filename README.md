# work
This is the repository my AI work sits inside.

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

# DocumentRootをProject Pathに変更
DocumentRoot "/Users/Path_To_Project_Files/public_html/"
ScriptAliasMatch ^/cgi-bin/((?!(?i:webobjects)).*$) "/Users/taharatakashi/AI/work/public_html/cgi-bin/$1"
# .htaccessを使用可能にする
<Directory >
　　　　AllowOverride All
＃ cgiの設定
mod_cgi.so, mod_userdir.so, mod_rewrite.soのコメントを外す
#AddHandler cgi~script .cgi をコメントを外し .pyを足す
Options FollowSymLinks Multiviews に ExecCGIを足す
# ApacheのUserを変更し、/Users/UserName/以下のファイルへアクセス可能にする
User _www => User (自らのUserName)

# Git clone
git clone https://github.com/temt-ceo/work.git
chmod 755 public_html

# Start Apache
sudo /usr/sbin/apachectl start

# flask インストール
python3 -m pip install --upgrade pip --user
python3 -m pip install Flask --user

# index.pyに以下の記述を追加
import site
site.addsitedir('/Users/taharatakashi/Library/Python/3.9/lib/python/site-packages')


# localhost確認

# git push
git push origin HEAD:main

```
