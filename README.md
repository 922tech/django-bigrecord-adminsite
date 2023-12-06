# django-bigrecord-adminsite
Django admin cannot load a model with too many records. So an optimized model is required to handle this case.
<br>
Just use the templates and static file and the `OptimizedAdminSearchMixin` class within the books application along with
its dependencies.
<br>
You can simply inherit the `OptimizedAdminSearchMixin` while creating an Admin class for your model.

