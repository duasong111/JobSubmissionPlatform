from django import forms
class BootStrapModelForm(forms.ModelForm):
    # 这个就是前边的那个钩子操作
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 循环ModelForm中的所有字段，给每个字段的插件设置
        for name, field in self.fields.items():
            # 字段中有属性，保留原来的属性，没有属性，才增加。
            # if field.widget.attrs:
            #     pass
			    # field.widget.attrs["class"] = "form-control"
				# field.widget.attrs["placeholder"] = field.label
            # else:

            #此处我进行的操作是不进行钩子的判断，不管是否有格式，我都进行重新定义这样的格式
                field.widget.attrs = {
                    "class": "form-control",
                    "placeholder": field.label
                }





class BootStrapForm(forms.Form):
    bootstrap_exclude_fields=[]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 循环ModelForm中的所有字段，给每个字段的插件设置
        for name, field in self.fields.items():
            if name in self.bootstrap_exclude_fields:
                continue
            if field.widget.attrs:
                field.widget.attrs["class"] = "form-control"
                field.widget.attrs["placeholder"] = field.label
            else:
                field.widget.attrs = {
                    "class": "form-control",
                    "placeholder": field.label
                }
