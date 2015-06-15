# graceful
`graceful` is documentation centered falcon REST toolkit. It is highly inspired
by [Django REST framework](http://www.django-rest-framework.org/) - mostly by
how object serialization is done but more emphasis here is put on API to
being self-descriptive.


# usage




# python3 only

**Important**: `graceful` is python3 exclusive. *Right now* is a good time to
forget about python2 and there are no plans for making `graceful` python2 
compatibile although it would be pretty straightforward do do so with existing
tools (like six).


# contributing

Any contribution is welcome. Issues, suggestions, pull requests - whatever. 
There is only short set of rules that guide this project development you
should be aware of before submitting a pull request:

* only requests that have passing CI builds (Travis) will be merged
* code is checked with flakes8 during build so this implicitely means that
  PEP-8 is a must
* no changes that decrease coverage will be merged

One thing: if you submit a PR please do not rebase it later unless you
are asked for that explicitely. Reviewing pull requests that suddenly had 
their history rewritten just drives me crazy.


# licence

See `LICENSE` file
