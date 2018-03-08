<h1 align="center">
    n_property
</h1>

<p align="center">
    n + 1 = 2
</p>
<p align="center">
  <a href="https://travis-ci.org/hrmthw/n_property">
    <img src="https://api.travis-ci.org/hrmthw/n_property.svg?branch=master" alt="build status">
  </a>
</p>

### 用法1：

```python
from n_property import n_class, n_property

@n_class
class Review(object):

    @n_property(fallback=None)
    def subject(selfs):
        subject_ids = [self.subject_id for self in selfs]
        return Subject.gets(subject_ids, filter_none=False)


reviews = Review.gets(review_ids)

print reviews[0].subject  # 第1次 Subject.gets 请求
print [r.subject for r in reviews]  # 触发批量prefetch，第2次 Subject.gets 请求
```


### 用法2 (more pythonic)：

```python
from n_property import n_class, n_property

@n_class
class Review(object):
    subject = n_property(fallback=None)
    
    @subject.n_getter
    @classmethod
    def get_subjects(cls, insts):
        subject_ids = [inst.subject_id for inst in insts]
        return Subject.gets(subject_ids, filter_none=False)


reviews = Review.gets(review_ids)

print reviews[0].subject  # 第1次 Subject.gets 请求
print [r.subject for r in reviews]  # 触发批量prefetch，第2次 Subject.gets 请求
```
