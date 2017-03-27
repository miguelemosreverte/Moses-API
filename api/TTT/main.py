# !/usr/bin/env python
# -*- coding: utf-8 -*-

##############################################################################
#
# PyKeylogger: TTT for Linux and Windows
# Copyright (C) 2016 Roxana Lafuente <roxana.lafuente@gmail.com>
#                    Miguel Lemos <miguelemosreverte@gmail.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


def install_and_import(package):
    import importlib
    try:
        importlib.import_module(package)
    except ImportError:
	try:
	        import pip
    	except ImportError:
		print "no pip"
		os.system('python get_pip.py')
	finally:
		import pip
        pip.main(['install', package])
    finally:
        globals()[package] = importlib.import_module(package)

#os is one of the modules that I know comes with 2.7, no questions asked.
import os
#these other ones I a am not so sure of. Thus the install function.
install_and_import("requests")
install_and_import("subprocess")
install_and_import("json")
install_and_import("sys")
install_and_import("time")
install_and_import("shutil")
install_and_import("urlparse")
install_and_import("itertools")

from commands import *
from files_processing import *
from constants import moses_dir_fn


UI_INFO = """
<ui>
  <menubar name='MenuBar'>
    <menu action='VisualsMenu'>
      <menu action='Visuals'>
        <menuitem action='metro'/>
        <menuitem action='paper'/>
        <separator />
        <menuitem action='lights_on_option'/>
      </menu>
    </menu>
  </menubar>
</ui>
"""

class TTT():

    def __init__(self):
        # Recognize OS
        if os.name == 'posix':  # Linux
            self.is_linux, self.is_windows = True, False
        elif os.name == 'nt':  # Windows
            self.is_linux, self.is_windows = False, True
        else:
            print "Unknown OS"
            exit(1)
        # Check Moses Config file.
        self.moses_dir = ""
        try:
            f = open(moses_dir_fn, 'r')
            self.moses_dir = f.read()
            f.close()
        except IOError, OSError:
            # File does not exist.
            self.moses_dir = self.get_moses_dir()
            f = open(moses_dir_fn, 'w')
            f.write(self.moses_dir)
            f.close()
        finally:
            # File content is wrong
            if not self.is_moses_dir_valid(self.moses_dir):
                moses_dir = self.get_moses_dir()
                f = open(moses_dir_fn, 'w')
                f.write(self.moses_dir)
                f.close()

        self.saved_absolute_path = os.path.abspath("saved")
        self.saved_relative_filepath = "./saved"
        if not os.path.exists(self.saved_absolute_path):
            os.makedirs(self.saved_absolute_path)

        # Init
        self.source_lang = None
        self.target_lang = None
        self.cwd = os.getcwd()

    def is_moses_dir_valid(self, directory):
        is_valid = True
        if directory == "":
            is_valid = False   # Empty string
        elif not os.path.exists(directory):
            is_valid = False  # Directory does not exist
        else:
            # Check if dir exists but does not contain moses installation
            is_valid = self._check_moses_installation(directory)

        return is_valid

    def _check_moses_installation(self, directory):
        # TODO: TRY catch OSError when permission denied!!
        file_content = [f for f in os.listdir(directory)]
        moses_files = ["/scripts/tokenizer/tokenizer.perl",
                       "/scripts/recaser/truecase.perl",
                       "/scripts/training/clean-corpus-n.perl",
                       "/bin/lmplz",
                       "/bin/build_binary",
                       "/scripts/training/train-model.perl",
                       "/bin/moses"
                      ]
        if self.is_windows:
            moses_files = [f.replace("/", "\\")
                           for f in moses_files]
            moses_files = [f + ".exe"
                           for f in moses_files
                           if "/bin" in f]
        is_valid = True
        for mfile in moses_files:
            is_valid = is_valid and os.path.isfile(directory + mfile)
        return is_valid

    def get_moses_dir(self):
        """
            Gets Moses directory.
        """
        self.moses_dir = "/home/moses/mosesdecoder"
        return self.moses_dir

    def _prepare_corpus(self, output_text, source_lang, target_lang, st_train, tt_train, lm_text):
        self.output_text = str(output_text)
        self.source_lang = str(source_lang)
        self.target_lang = str(target_lang)
        self.lm_text = str(lm_text)
        self.tt_train = str(tt_train)
        self.st_train = str(st_train)
        """@brief     Runs moses truecaser, tokenizer and cleaner."""
        output = ""
        output_directory = adapt_path_for_cygwin(self.is_windows, self.output_text)
        if output_directory is not None:
            # Change directory to the output_directory.
            try:
                os.chdir(self.output_text)
            except:
                # Output directory does not exist.
                os.mkdir(self.output_text)
                os.chdir(self.output_text)
            cmds = []
            # 1) Tokenization
            # a) Target text
            self.target_tok = generate_input_tok_fn(self.target_lang,
                                                    output_directory)
            cmds.append(get_tokenize_command(adapt_path_for_cygwin(self.is_windows, self.moses_dir),
                                             self.target_lang,
                                             adapt_path_for_cygwin(self.is_windows, self.tt_train),
                                             self.target_tok))
            # b) Source text
            self.source_tok = generate_input_tok_fn(self.source_lang,
                                                    output_directory)
            cmds.append(get_tokenize_command(adapt_path_for_cygwin(self.is_windows, self.moses_dir),
                                             self.source_lang,
                                             adapt_path_for_cygwin(self.is_windows, self.st_train),
                                             self.source_tok))
            # c) Language model
            self.lm_tok = generate_lm_tok_fn(output_directory)
            cmds.append(get_tokenize_command(adapt_path_for_cygwin(self.is_windows, self.moses_dir),
                                             self.source_lang,
                                             adapt_path_for_cygwin(self.is_windows,self.lm_text),
                                             self.lm_tok))

            # 2) Truecaser training
            # a) Target text
            cmds.append(get_truecaser_train_command(adapt_path_for_cygwin(self.is_windows, self.moses_dir),
                                                    output_directory,
                                                    self.target_lang,
                                                    self.target_tok))
            # b) Source text
            cmds.append(get_truecaser_train_command(adapt_path_for_cygwin(self.is_windows, self.moses_dir),
                                                    output_directory,
                                                    self.source_lang,
                                                    self.source_tok))
            # c) Language model
            cmds.append(get_truecaser_train_command(adapt_path_for_cygwin(self.is_windows, self.moses_dir),
                                                    output_directory,
                                                    self.target_lang,
                                                    self.lm_tok))

            # 3) Truecaser
            self.input_true = output_directory + "/input.true"
            # a) Target text
            self.target_true = generate_input_true_fn(self.target_lang,
                                                      output_directory)
            cmds.append(get_truecaser_command(adapt_path_for_cygwin(self.is_windows, self.moses_dir),
                                              output_directory,
                                              self.target_lang,
                                              self.target_tok,
                                              self.target_true))
            # b) Source text
            self.source_true = generate_input_true_fn(self.source_lang,
                                                      output_directory)
            cmds.append(get_truecaser_command(adapt_path_for_cygwin(self.is_windows, self.moses_dir),
                                              output_directory,
                                              self.source_lang,
                                              self.source_tok,
                                              self.source_true))
            # c) Language model
            self.lm_true = generate_lm_true_fn(output_directory)
            cmds.append(get_truecaser_command(adapt_path_for_cygwin(self.is_windows, self.moses_dir),
                                              output_directory,
                                              self.target_lang,
                                              self.target_tok, self.lm_true))

            # 4) Cleaner
            # a) Target text
            self.input_clean = generate_input_clean_fn(output_directory)
            self.source_clean = self.input_true + "." + self.source_lang
            self.target_clean = self.input_true + "." + self.target_lang
            cmds.append(get_cleaner_command(adapt_path_for_cygwin(self.is_windows, self.moses_dir),
                                            self.source_lang,
                                            self.target_lang,
                                            self.input_true,
                                            self.input_clean))

            # Start threads
            all_ok = True
            for cmd in cmds:
                output += "Running command: %s" % cmd + "\n\n"
                proc = subprocess.Popen([cmd],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        shell=True)
                all_ok = all_ok and (proc.wait() == 0)
                out, err = proc.communicate()
                output += "Output: %s\n%s\n\n\n" % (out, err)

            if all_ok:
                self.is_corpus_preparation_ready = True
                with open(output_directory + '/lm.ini', 'w') as f:
                    f.write("source_lang:"+self.source_lang+"\n")
                    f.write("target_lang:"+self.target_lang+"\n")
        else:
            output += "ERROR. You need to complete all fields."
        return output

    def _train(self):
        # print "==============================>", self.is_corpus_preparation_ready
        print self.output_text
        output_directory = adapt_path_for_cygwin(self.is_windows, self.output_text)
        output = ""
        if output_directory is not None and self.is_corpus_preparation_ready:
            cmds = []
            output = "Log:\n\n"
            # Train the language model.
            self.lm_arpa = generate_lm_fn(output_directory)
            print "out:", self.lm_arpa, "\n"
            cmds.append(get_lmtrain_command(self.moses_dir,
                                            self.target_lang,
                                            self.lm_true,
                                            self.lm_arpa))

            # Binarize arpa
            self.blm = generate_blm_fn(output_directory)
            print "binarized out:", self.blm, "\n"
            cmds.append(get_blmtrain_command(self.moses_dir,
                                             self.target_lang,
                                             self.lm_arpa,
                                             self.blm))


            # Train the translation model.
            out_file = generate_tm_fn(output_directory)
            cmds.append(get_tmtrain_command(self.moses_dir,
                                             self.source_lang,
                                            self.target_lang,
                                            self.blm,
                                            self.input_clean,
                                            output_directory))

            # TODO!
            # Binarize phase-table.gz
            # Binarize reordering-table.wbe-msd-bidirectional-fe.gz
            # Change PhraseDictionaryMemory to PhraseDictionaryCompact
            # Set the path of the PhraseDictionary feature to point to $HOME/working/binarised-model/phrase-table.minphr
            # Set the path of the LexicalReordering feature to point to $HOME/working/binarised-model/reordering-table

            for cmd in cmds:
                # use Popen for non-blocking
                print cmd
                output += cmd + "\n"
                proc = subprocess.Popen([cmd],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        shell=True)
                proc.wait()
                (out, err) = proc.communicate()
                if out != "":
                    output += out
                elif err != "":
                    output += err

            # Adding output from training.out
            training = adapt_path_for_cygwin(self.is_windows, self.output_text) + "/training.out"
            try:
                with open(training, "r") as f:
                   output += "\n" + f.read()
            except IOError:pass

            # Set output to the output label.
        else:
            output = "ERROR: Please go to the first tab and complete the process."
        return output

    def _machine_translation(self, mt_in):
        base=os.path.basename(mt_in)
        mt_out = os.path.dirname(mt_in) +  os.path.splitext(base)[0] + "_translated" + os.path.splitext(base)[1]
        in_file = adapt_path_for_cygwin(self.is_windows, mt_in)
        out_file = adapt_path_for_cygwin(self.is_windows,mt_out)
        output = "Running decoder....\n\n"
        # Run the decoder.
        cmd = get_test_command(self.moses_dir,
                                   adapt_path_for_cygwin(self.is_windows, self.output_text) + "/train/model/moses.ini",
                                   in_file,
                                   out_file)
        # use Popen for non-blocking
        #print cmd
        proc = subprocess.Popen([cmd],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    shell=True)
        (out, err) = proc.communicate()
        f = open(out_file, 'r')
        mt_result = f.read()
        if mt_result == "":
                if out != "":
                    output += out
                elif err != "":
                    output += err
        else:
                output += "Best translation: " + mt_result

        f.close()
        return output
