# A python proxy made from the stdlib

This is made to work with the latest versions of python, I've adapted it from [this gist](https://gist.github.com/darkwave/52842722c0c451807df4) and have tested with python 3.7 and 3.8.

It's not yet been production hardened and is very basic, but hopefully it's simple enough that you can adapt it to your needs. I've been using to give more control over the proxy used by a selenium web browser and it does what I need, although being single-threaded brings a noticeable performance impact.
