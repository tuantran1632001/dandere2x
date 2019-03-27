import configparser
import os
import subprocess
import threading

from Dandere2xCppWrapper import Dandere2xCppWrapper
from Difference_Script import difference_loop
from Merge_Script import merge_loop
from Waifu2xCaffe import Waifu2xCaffe
from ffmpeg import extract_frames


class Dandere2x:
    def __init__(self, config_file):
        config = configparser.ConfigParser()
        config.read(config_file)

        self.waifu2x_caffe_cui_dir = config.get('dandere2x', 'waifu2x_caffe_cui_dir')
        self.workspace = config.get('dandere2x', 'workspace')
        self.file_dir = config.get('dandere2x', 'file_dir')
        self.dandere2x_cpp_dir = config.get('dandere2x', 'dandere2x_cpp_dir')
        self.ffmpeg_dir = config.get('dandere2x', 'ffmpeg_dir')
        self.time_frame = config.get('dandere2x', 'time_frame')
        self.duration = config.get('dandere2x', 'duration')
        self.audio_layer = config.get('dandere2x', 'audio_layer')
        self.frame_rate = config.get('dandere2x', 'frame_rate')
        self.width = config.get('dandere2x', 'width')
        self.height = config.get('dandere2x', 'height')
        self.block_size = int(config.get('dandere2x', 'block_size'))
        self.tolerance = config.get('dandere2x', 'tolerance')
        self.step_size = config.get('dandere2x', 'step_size')
        self.bleed = config.get('dandere2x', 'bleed')
        self.psnr_low = config.get('dandere2x', 'psnr_low')
        self.psnr_high = config.get('dandere2x', 'psnr_high')
        self.noise_level = config.get('dandere2x', 'noise_level')
        self.scale_factor = config.get('dandere2x', 'scale_factor')
        self.process_type = config.get('dandere2x', 'process_type')
        self.dandere_dir = config.get('dandere2x', 'dandere_dir')

        self.file_location = self.workspace + "inputs" + os.path.sep
        self.out_location = self.workspace + "outputs" + os.path.sep
        self.upscaled_location = self.workspace + "upscaled" + os.path.sep
        self.merged_dir = self.workspace + "merged" + os.path.sep
        self.inversion_data_dir = self.workspace + "inversion_data" + os.path.sep
        self.pframe_data_dir = self.workspace + "pframe_data" + os.path.sep
        self.debug_dir = self.workspace + "debug" + os.path.sep
        self.log_dir = self.workspace + "logs" + os.path.sep

        self.frame_count = 240

    def run(self):
        self.create_dirs()
        self.extract_frames()
        # self.start_dandere2x_cpp()
        self.create_waifu2x_script()
        self.write_frames()

        waifu2x = Waifu2xCaffe(self.frame_count, self.waifu2x_caffe_cui_dir, self.out_location, self.upscaled_location,
                                "cudnn", "3", "2.0")
        d = Dandere2xCppWrapper(self.workspace, self.dandere2x_cpp_dir, self.frame_count, self.block_size,
                                self.tolerance, self.psnr_high, self.psnr_low, self.step_size)

        merge_thread = threading.Thread(target=merge_loop, args=(self.workspace, self.frame_count, self.block_size))
        difference_thread = threading.Thread(target=difference_loop,
                                             args=(self.workspace, self.frame_count, self.block_size))

        Waifu2xCaffe.upscale_file(self.waifu2x_caffe_cui_dir, self.file_location + "frame1.jpg",
                                  self.merged_dir + "merged_1.jpg", "cudnn", "3", "2.0")
        waifu2x.start()

        merge_thread.start()
        difference_thread.start()
        d.start()

        merge_thread.join()
        d.join()
        difference_thread.join()

    def dif_thread(self):
        difference_thread = threading.Thread(target=difference_loop,
                                             args=(self.workspace, self.frame_count, self.block_size))
        difference_thread.start()

    def create_dirs(self):

        directories = {self.workspace, self.file_location, self.out_location, self.upscaled_location,
                       self.merged_dir, self.upscaled_location, self.merged_dir, self.inversion_data_dir,
                       self.pframe_data_dir, self.debug_dir, self.log_dir}

        for subdirectory in directories:
            try:
                os.mkdir(subdirectory)
            except OSError:
                print("Creation of the directory %s failed" % subdirectory)
            else:
                print("Successfully created the directory %s " % subdirectory)

    def extract_frames(self):
        extract_frames(self.time_frame, self.file_dir, self.frame_rate, self.duration, self.workspace)

    def create_waifu2x_script(self):

        input_list = []
        input_list.append("cd /home/linux/Documents/waifu2x/")

        input_list.append(
            "th " + self.dandere_dir + " -m noise_scale -noise_level 3 -i " + self.file_location + "frame1.jpg" +
            " -o " + self.merged_dir + "merged_1.jpg\n")

        input_list.append("th " + self.dandere_dir + " -m noise_scale -noise_level 3 -resume 1 -l "
                          + self.workspace + "frames.txt -o " + self.upscaled_location + "output_%d.png")

        with open(self.workspace + os.path.sep + 'waifu2x_script.sh', 'w') as f:
            for item in input_list:
                f.write("%s\n" % item)

        os.chmod(self.workspace + os.path.sep + 'waifu2x_script.sh', 0o777)

    def start_waifu2x_script(self):
        subprocess.call(["bash", "-c", self.workspace + os.path.sep + 'waifu2x_script.sh'])

    def start_dandere2x_cpp(self):
        cpp = Dandere2xCppWrapper(self.workspace, self.dandere2x_cpp_dir, self.frame_count, self.block_size,
                                  self.tolerance, self.psnr_high, self.psnr_low, self.step_size)
        cpp.start()

    def write_frames(self):
        with open(self.workspace + os.path.sep + 'frames.txt', 'w') as f:
            for x in range(1, self.frame_count):
                f.write(self.out_location + "output_" + str(x) + ".png\n")

    def make_dif(self):
        difference_loop(self.workspace, self.frame_count)

    def merge(self):
        merge_loop(self.workspace, self.frame_count)
