from tkinter import Tk, Frame, Scale, Label, Button, filedialog, messagebox, HORIZONTAL, Checkbutton, IntVar, Entry
from PIL import Image, ImageTk, ImageFilter
import svgwrite
import numpy as np
import os

class ImageProcessor:
    def __init__(self):
        # 创建主窗口
        self.master = Tk()
        self.master.title("Image Processor")

        # 默认设置
        self.image_path = None
        self.output_path = None
        self.target_width=127
        self.noise_reduction_level = 0  # 初始噪声减少强度

        # 创建颜色过滤复选框
        self.color_filters = {
            "Red": IntVar(),
            "Yellow": IntVar(),
            "White": IntVar(),  # 改为白色
            "Black": IntVar()
        }

        # 创建 UI 组件
        self.create_widgets()

        # 启动 Tkinter 主循环
        self.master.mainloop()

    def create_widgets(self):
        # 选择图像按钮
        self.choose_button = Button(self.master, text="Choose Image", command=self.choose_image)
        self.choose_button.pack()

        # 创建预览框架
        self.preview_frame = Frame(self.master)
        self.preview_frame.pack()

        # 显示处理后的图像
        self.preview_label = Label(self.preview_frame)
        self.preview_label.pack()

        # 宽度输入框
        self.target_width_label = Label(self.master, text="输入宽度(mm) max 254:")
        self.target_width_label.pack()
        self.target_width_entry = Entry(self.master)
        self.target_width_entry.insert(127, str(self.target_width))  # 设置初始值
        self.target_width_entry.pack()

        # 监听宽度输入框的变化，触发图像更新
        self.target_width_entry.bind("<KeyRelease>", self.update_image)

        # 噪声减少强度调整滑块
        self.noise_reduction_label = Label(self.master, text="Adjust Noise Reduction Level:up down")
        self.noise_reduction_label.pack()
        self.noise_reduction_scale = Scale(self.master, from_=0, to_=10, orient=HORIZONTAL, command=self.update_image)
        self.noise_reduction_scale.set(self.noise_reduction_level)
        self.noise_reduction_scale.pack()

        # 颜色过滤复选框
        self.filter_label = Label(self.master, text="Select Colors to Exclude:")
        self.filter_label.pack()

        for color, var in self.color_filters.items():
            checkbutton = Checkbutton(self.master, text=color, variable=var)
            checkbutton.pack()

        # 保存按钮
        self.save_button = Button(self.master, text="Save Image", command=self.save_image)
        self.save_button.pack()

        # 保存为四种颜色独立 SVG 的按钮
        self.save_svg_button = Button(self.master, text="Save as Separate SVGs", command=self.save_as_separate_svgs)
        self.save_svg_button.pack()

        # 键盘事件绑定
        self.master.bind("<Up>", lambda event: self.update_noise_reduction(1))
        self.master.bind("<Down>", lambda event: self.update_noise_reduction(-1))

    def choose_image(self):
        """打开文件对话框，选择图像。"""
        self.image_path = filedialog.askopenfilename(title="Select an Image", filetypes=[("Image Files", "*.jpg;*.jpeg;*.png;*.bmp")])
        if self.image_path:
            self.image = Image.open(self.image_path).convert("RGBA")
            self.update_image()  # 加载选中图像

    def resize_image(self, image):
        """根据当前缩放比例调整图像大小。"""
        new_width = int((float(self.target_width)/(25.4/96)))
        width_percent = (new_width / float(image.size[0]))
        new_height = int((float(image.size[1]) * float(width_percent)))
        return image.resize((new_width, new_height))

    def apply_noise_reduction(self, image, level):
        """应用噪声减少效果（高斯模糊）"""
        if level > 0:
            # 高斯模糊，根据强度调整模糊半径
            return image.filter(ImageFilter.GaussianBlur(radius=level))
        return image

    def closest_color(self, r, g, b, a):
        """将每个像素颜色映射到最接近的红、黄、白、黑四种颜色。"""
        colors = {
            "Red": (255, 0, 0),
            "Yellow": (255, 255, 0),
            "White": (255, 255, 255),  # 改为白色
            "Black": (0, 0, 0)
        }
        min_distance = float('inf')
        closest_color = (255, 255, 255)  # 默认为白色
        for color_name, color in colors.items():
            distance = np.sqrt((r - color[0]) ** 2 + (g - color[1]) ** 2 + (b - color[2]) ** 2)
            if distance < min_distance:
                min_distance = distance
                closest_color = color
        return (*closest_color, a)

    def update_image(self, event=None):
        """根据当前缩放比例和噪声减少强度更新显示图像。"""
        if self.image_path:
            self.target_width = self.target_width_entry.get()
            self.noise_reduction_level = self.noise_reduction_scale.get()

            if int(self.target_width) <255:
                self.resized_image = self.resize_image(self.image)
                self.resized_image = self.apply_noise_reduction(self.resized_image, self.noise_reduction_level)  # 应用噪声减少

                # 将每个像素的颜色映射到四种颜色
                pixels = self.resized_image.load()
                width, height = self.resized_image.size

                print('resize后， 调色前',pixels[width-1, height-1])
                has_transparent = any(pixels[x, y][3] < 255 for x in range(width) for y in range(height))

                if has_transparent:
                    print("The image contains transparent pixels.")
                else:
                    print("The image is fully opaque (no transparency).")

                for y in range(height):
                    for x in range(width):
                        r, g, b, a = pixels[x, y]
                        pixels[x, y] = self.closest_color(r, g, b, a)

                print('调色后',pixels[width-1, height-1])
                has_transparent = any(pixels[x, y][3] < 255 for x in range(width) for y in range(height))

                if has_transparent:
                    print("The image contains transparent pixels.")
                else:
                    print("The image is fully opaque (no transparency).") 

                # 显示转换后的图像
                self.photo = ImageTk.PhotoImage(self.resized_image)
                self.preview_label.config(image=self.photo)
                self.preview_label.image = self.photo

    def update_noise_reduction(self, increment):
        """根据键盘事件调整噪声减少强度。"""
        new_noise_reduction = self.noise_reduction_level + increment
        if 0 <= new_noise_reduction <= 10:
            self.noise_reduction_level = new_noise_reduction
            self.noise_reduction_scale.set(self.noise_reduction_level)
            self.update_image()

    def save_image(self):
        """保存处理后的图像。"""
        if self.resized_image:
            save_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("JPEG files", "*.jpg"), ("PNG files", "*.png")])
            if save_path:
                self.resized_image.save(save_path)
                messagebox.showinfo("成功", "Image saved successfully!")

    def save_as_separate_svgs(self):
        """将图像分成四个独立的 SVG 文件，分别保存四种颜色。"""
        #颜色打印顺序
        print_turn_dict={"Black":'1st',"Red":'2nd',"Yellow":'3rd',"White":'4th'}

        if self.resized_image:
            # 创建保存路径选择对话框
            save_folder = filedialog.askdirectory(title="Select Folder to Save SVGs")
            if not save_folder:
                return

            # 获取原始图像文件名，不包括扩展名
            base_filename = os.path.splitext(os.path.basename(self.image_path))[0]

            width, height = self.resized_image.size
            pixels = self.resized_image.load()

            print('输出时',pixels[width-1, height-1])

            # 根据复选框状态定义要导出的颜色
            export_colors = {}
            if self.color_filters["Red"].get() == 1:
                export_colors["Red"] = (255, 0, 0)
            if self.color_filters["Yellow"].get() == 1:
                export_colors["Yellow"] = (255, 255, 0)
            if self.color_filters["White"].get() == 1:  # 改为白色
                export_colors["White"] = (255, 255, 255)
            if self.color_filters["Black"].get() == 1:
                export_colors["Black"] = (0, 0, 0)

            if not export_colors:
                messagebox.showwarning("Warning", "No colors selected for export!")
                return

            # 对每种颜色单独导出一个 SVG 文件
            
            for color_name, color in export_colors.items():
                count=print_turn_dict[color_name]
                svg_filename = f"{base_filename}_{color_name}_{count}.svg"
                svg_path = os.path.join(save_folder, svg_filename)

                dwg = svgwrite.Drawing(svg_path, size=(width, height))

                # 绘制图片边框
                dwg.add(dwg.rect(insert=(0, 0), size=(width, height), fill='none', stroke='black', stroke_width=0.01))

                # 存储所有需要绘制的矩形
                rectangles = []

                # 合并连续像素为矩形
                for y in range(height):
                    x_start = None
                    for x in range(width):
                        r, g, b, a = pixels[x, y]

                        if a == 0 and x_start is not None:
                            # 跳过透明像素
                            rectangles.append((x_start, y, x - x_start, 1))
                            x_start = None
                        if a==0:
                            continue 

                        if r+g+b>=color[0]+color[1]+color[2]:
                            if x_start is None:
                                x_start = x  # 开始记录连续像素段
                        else:
                            if x_start is not None:
                                # 结束记录，创建矩形
                                rectangles.append((x_start, y, x - x_start, 1))
                                x_start = None
                    # 处理行尾的连续像素
                    if x_start is not None:
                        rectangles.append((x_start, y, width - x_start, 1))

                # 添加合并后的矩形到SVG
                for x, y, w, h in rectangles:
                    if w > 0:
                        dwg.add(dwg.rect(insert=(x, y), size=(w, h), fill=svgwrite.rgb(*color)))

                # 保存该颜色的 SVG 文件
                dwg.save()

                # Create PNG image for the selected color
                img_filename = os.path.join(save_folder, f"{base_filename}_{color_name}_{count}.png")
                color_img = Image.new("RGB", (width, height), (255, 255, 255))

                # Use rectangles to fill the image
                for x, y, w, h in rectangles:
                    if w > 0:  # Only add rectangles that are large enough
                        for i in range(w):  # Fill each pixel in the rectangle
                            for j in range(h):  # Fill each pixel in the rectangle
                                color_img.putpixel((x + i, y + j), color)

                color_img.save(img_filename)


            messagebox.showinfo("成功", "SVGs and Images saved successfully!")
   
if __name__ == "__main__":
    app = ImageProcessor()
