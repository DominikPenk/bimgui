import os
import re
import gpu

class ReloadingShader:
    '''
    A class that wraps loading shaders from files.
    This will try to reload shader on bind if the source file was updated.
    This causes overhead so only use this class during development
    '''
    def __init__(self, filename):
        self.filename = filename
        self._last_modified = 0
        self._shader = None
        #pylint: disable=invalid-name
        self.re = re.compile("//\\s*--(\\w+)\\s*[\\n\\r]+")
        self.reload_shaders()

    def reload_shaders(self):
        '''
        Reloads the shader from its source if it was updated since the last load.
        '''
        last_modified = os.stat(self.filename).st_mtime

        if self._last_modified < last_modified:
            with open(self.filename) as src_file:
                src = src_file.read()
            # print(src)
            shaders = {}
            preamble = ""
            last_type = ""
            while True:
                match = self.re.search(src)
                if match is None:
                    break
                if shaders:
                    # print("Source:\n{}".format(src[ : match.start()]))
                    shaders[last_type] = preamble + src[:match.start()]
                else:
                    # print("Preamble: {}".format(src[: match.start()]))
                    preamble = src[:match.start()]
                # print("shader: {}".format(match[1]))
                shaders[match[1]] = ""
                last_type = match[1]
                src = src[match.end():]
            if shaders:
                # print("Source:\n{}".format(src))
                shaders[last_type] = preamble + src

            fragment_shader = shaders.get('fragment', "")
            vertex_shader = shaders.get('vertex', "")
            shaders.pop('vertex', None)
            shaders.pop('fragment', None)

            self.shader = gpu.types.GPUShader(vertex_shader,
                                              fragment_shader,
                                              **shaders)

            self._last_modified = last_modified

    def bind(self):
        '''
        Binds the shader and reloads it neccessary
        '''
        self.reload_shaders()
        self.shader.bind()

    def attr_from_name(self, name):
        return self.shader.attr_from_name(name)

    def uniform_block_from_name(self, name):
        return self.shader.uniform_block_from_name(name)

    def uniform_bool(self, name, seq):
        return self.shader.uniform_bool(name, seq)

    def uniform_float(self, name, value):
        self.shader.uniform_float(name, value)

    def uniform_from_name(self, name):
        return self.shader.uniform_from_name(name)

    def uniform_int(self, name, val):
        self.shader.uniform_int(name, val)

    def uniform_vector_float(self, location, buffer, length, count):
        self.shader.uniform_vector_float(location, buffer, length, count)

    def uniform_vector_int(self, location, buffer, length, count):
        self.shader.uniform_vector_int(location, buffer, length, count)

def get_shader(shader):
    path = os.path.abspath(os.path.join("./shaders", "{}.glsl".format(shader)))
    print("Loading shader {}".format(path))
    return ReloadingShader(path)