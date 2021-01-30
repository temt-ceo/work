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

# Apache 設定
which httpd
which apachectl
sudo vi /etc/apache2/httpd.conf
# DocumentRootをProject Pathに変更
# DocumentRoot "/Users/Path_To_Project_Files/public_html/"

# Git clone
git clone https://github.com/temt-ceo/work.git

# Apache 起動
sudo /usr/sbin/apachectl start

# localhost確認

```
