# texteditwx

数式処理システムMaximaの簡易フロントエンドPythonスクリプトです．
Shift+EnterでMaximaコマンドを評価します．上下を空行で挟まれた部分，または選択部分をMaximaコマンドとして解釈します．
EscキーでMaximaコマンドのショートカットが使えるようになります．
その他，OpenFOAMの境界条件の雛形を挿入できます．

フォルダごとダウンロードして，texteditwx.pyをPythonで実行して下さい．

当然ですが，Maximaの機能を使うためには，Maximaをインストールする必要があります．
デフォルトでインストールしている場合は大丈夫ですが，Maximaが起動しない場合はMaximaへのパスが間違っている可能性が大きいです．
texteditwx.pyの上側に書いてある，maxima\_location = の右辺を正しいパスに修正して下さい．

以下のモジュールをpipでダウンロードして下さい：
```
pip install wxPython pyperclip requests pexpect zenhan
```

texteditwxは[ここ](https://github.com/gitwamoto/texteditwxx)からダウンロードできます．
