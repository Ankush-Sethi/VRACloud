def handler(context, inputs):
    output = inputs
    print(output)
    output['initialPowerOn'] = 'false'
    return output
