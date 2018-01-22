import os, sys, optparse, re, glob, shutil, difflib, socket

class Config:

  def __init__(self, path) :
    self.path = path
    self.lines = []
    self.map = {}
    self.kv = {}

    if path:
      if path.endswith("json"): 
        self.delimiter = ":"
      else:
        self.delimiter = '='

      #if os.path.isfile(path + ".orig"):
      #  f = open(path + ".orig", "r")
      #else:
      f = open(path, "r")
      self.read(f)
      f.close()
    else :
      self.delimiter = '='

  def read(self, f) :
    for line in f:
      line = line.rstrip()

      self.lines.append(line)
      if len(line) != 0 and line[0] != '#':
        key,sep,value = getKey(line, self.delimiter)
        lens = len(self.lines)
        if value != '{' and value != '[' :
          self.map[key] = lens
          self.kv[key] = value

  def write(self, path) :
    text = ''
    for line in self.lines :
      if not line.endswith("\n"):
        line += "\n"
      text += line
    write_to_file(path, text, 'w') 

  def replace(self, key, newValue) :
    id = self.map[key]
    if not id:
      return
    id -= 1
    line = self.lines[id]

    newLine = ''
    for ch in line:
      if ch == ' ':
        newLine += ch
      else:
        break

    if self.delimiter == ':' :
      # FIXME: if origin line has "," we add "," too.
      newLine += '\"' + key + '\" ' +  self.delimiter + ' \"' + newValue + '\",'
    else :
      newLine += key + self.delimiter + newValue
    self.lines[id] = newLine

  def get(self, key) :
    return self.kv[key]

  def exists(self, key) :
    return key in self.map

  def getMap(self) :
    return self.kv


# -----------------------------------------------------------------------------
def main():
  # Process command line arguments
  (verbose, configfile, envFile, env, top) = process_options()

  # Load custom configuration file
  if not os.path.isfile(configfile):
    die("ERROR: config file %s not found" % configfile)
  CONFIG = eval(open(configfile).read())
  ENVS = eval(open(envFile).read())

  # process env inheritance relationship
  solveEnvDependencies(ENVS)

  if env not in ENVS :
    die("Error: %s not in ENVS." % env)


  ENV = ENVS[env]
  TOP = top

  pattern = re.compile(r"\$\{[a-zA-Z_0-9-\.]+\}")

  for name in CONFIG:
    if name == '__TOP__': 
      continue

    print "Process component: %s" % name
    component = CONFIG[name]
    componentPath = TOP + "/" + name

    for cfg in component:
      path = cfg['path']
      path = componentPath + "/" + path

      # create backup first
      if verbose:
        print "%s: Replacing file %s" % (name , path)

      if 'replacement' in cfg: 
        replacements = cfg['replacement']
        config = Config(path)

        for key in replacements:
          newValue = replacements[key]
          newValue = replace(key, newValue, pattern, ENV)

          if verbose:
            print "Replace key: %s, orig: %s, new: %s" % (key, config.get(key), newValue) 
          config.replace(key, newValue)
        # end for

        config.write(path)
      elif 'all' in cfg:
        replaceAll = cfg['all']
        replaceAll = replace('', replaceAll, pattern, ENV)
        print "Replace All file: %s, new: %s" % (path, replaceAll)
        allText = replaceAll
        write_to_file(path, allText, 'w')

    # end for
  # end for

  # output all ENV dir

  text = ''
  for key in ENV:
    newValue = ENV[key]
    newValue = replace(key, newValue, pattern, ENV)
    text += key + "=" + newValue + "\n"

  write_to_file(top + "/all_dirs.conf", text, 'w') 


def solveEnvDependencies(ENVS):
  for curName in ENVS:
    solveEnvExtends(curName, ENVS[curName], ENVS)

def solveEnvExtends(name, node, ENVS):
  if '__EXTENDS__' in node:
    parentName = node['__EXTENDS__']
    print "Env %s extends %s" % (name, parentName)
    if parentName in ENVS:
      parent = ENVS[parentName]
      parent = solveEnvExtends(parentName, parent, ENVS)
      for key in parent:
        if key not in node:
          node[key] = parent[key]
    else:
      die("Error: not found base env name: %s in envs.json" % parentName)

  return node
#------------------------------------------------------------------
def replace(key, newValue, pattern, ENV):
  matches = pattern.findall(newValue)

  if matches:
    for match in matches:
      envKey = match[2:-1]
      if envKey in ENV.keys() :
        modifyValue = ENV[envKey]
        newValue = newValue.replace(match, modifyValue)
      else :
        die("Error: not found %s in ENV file" % envKey)

    # support recursion ${} definition
    newValue = replace(key, newValue, pattern, ENV)
  # end if

  return newValue

#------------------------------------------------------------------
def write_to_file(filename, output, mode='w'):
  'Write output to file after saving the original file'

  dest = filename + ".orig"

  if not os.path.exists(dest) and os.path.exists(filename):
    shutil.copyfile(filename, dest)

  f = open(filename, mode)
  f.write(output)
  f.close()


# -----------------------------------------------------------------------------
def process_options():
  'Process command parameters'

  usage = "%s [-h|-v|-d] [--config CONFIG] [--env ENV]" % sys.argv[0]

  parser = optparse.OptionParser(usage = usage)
  parser.add_option('-v', '--verbose', dest='verbose', default=False, action="store_true",
                    help="verbose mode")
  parser.add_option('-c', '--config', dest='configfile',
                    help="Path to configuration file.  Defaults to ./dib_update_config.conf.")
  parser.add_option('-n', '--econfig', dest='envFile',
                    help="Path to configuration file.  Defaults to ./dib_update_config.conf.")
  parser.add_option('-e', '--env', dest='env',
                    help="environment to deploy to.  Can be set by ENVIRONMENT env var.")
  parser.add_option('-t', '--top', dest='top',
                    help="top dir to deploy to.")

  (opts, args) = parser.parse_args()
  verbose = opts.verbose
  if opts.configfile:
    configfile = opts.configfile
  else:
    die("ERROR: --config not set.")

  if opts.envFile:
    envFile = opts.envFile
  else:
    die("ERROR: --econfig not set.")

  if opts.env:
    env = opts.env
  else:
    die("ERROR: --env not set.")

  if opts.top:
    top = opts.top
  else:
    die("ERROR: --env not set.")

  return (verbose, configfile, envFile, env, top)

# -----------------------------------------------------------------------------
def getKey(line, delimiter):
  tokens = line.split(delimiter, 2)

  # process "KEY" : "VALUE",  to KEY, VALUE
  if delimiter == ":":
    temp = []
    for t in tokens:
      temp.append(t.strip()[1:-1])
    tokens = temp

  if len(tokens) == 1:
    return tokens[0].strip(), "", ""
  else:
    return tokens[0].strip(), delimiter, tokens[1].strip()


# -----------------------------------------------------------------------------
def die(message):
  'Print error message and exit with error code'
  print message
  sys.exit(1)

if __name__ == "__main__":
  sys.exit(main())

