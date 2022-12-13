def handler(context, inputs):
    custom_tag = []
    current_tag = list(inputs['customProperties']['custom_tag'])
    print(current_tag)
    custom = {}
    for i in current_tag:
        print(i)
    #     custom[i['key']]=i['value']
    # print(custom)
    # output['customProperties']['custom_tag'] = custom
    # return output
