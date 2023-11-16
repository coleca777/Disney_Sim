import json
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
import shutil
from zipfile import ZipFile

def normalize(aList):
    for value in aList.values():
        normList = np.array(value["peopleList"])
        norm = np.linalg.norm(normList)
        if np.max(normList) != 0:
            value["peopleList"] = normList / np.max(normList)
    return aList


def graph_vis(config):
    f = open(config)
    data = json.load(f)

    edges = data['edges']
    points = data['points']

    edges = normalize(edges)
    points = normalize(points)

    # Extract the lists of x, y, and color data
    x_data = [point["longitude"] * -1 for point in points.values()]
    y_data = [point["latitude"] for point in points.values()]
    color_data = [point["peopleList"] for point in points.values()]
    color_init = [c[0] for c in color_data]

    max_value = max(max(color) for color in color_data)

    cmap = LinearSegmentedColormap.from_list("Custom", ["darkblue", "red"])

    # Create a figure and axis for the heatmap
    fig, ax = plt.subplots()
    plt.subplots_adjust(bottom=0.25)

    # Create a scatter plot for the points with a colormap based on the color_data
    sc = plt.scatter(x_data, y_data, c=color_init, cmap=cmap, s=50, vmin=0, vmax=max_value)

    # Add labels for the points
    for name, point in points.items():
        plt.text(point["longitude"] * -1, point["latitude"], name, fontsize=6, ha='center', va='bottom')

    # Draw the edges
    edge_lines = []

    for edge in edges:
        p1_name, p2_name = edge.split("/")
        point1 = (points[p1_name]["longitude"] * -1, points[p1_name]["latitude"])
        point2 = (points[p2_name]["longitude"] * -1, points[p2_name]["latitude"])
        line, = plt.plot([point1[0], point2[0]], [point1[1], point2[1]], 'k-')
        edge_lines.append(line)

    plt.axis('off')
    plt.title("Magic Kingdom Map")

    # Create a color scale
    cax = fig.add_axes([0.9, 0.3, 0.03, 0.4])
    cb = plt.colorbar(sc, cax=cax)
    cb.set_label("Color Scale")

    # Create a slider for selecting the index
    axcolor = 'lightgoldenrodyellow'
    axindex = plt.axes([0.2, 0.01, 0.65, 0.03], facecolor=axcolor)

    # Set the valstep parameter to display only integer values
    slider = Slider(axindex, 'Index', 0, 840, valinit=0, valstep=1)

    def update(val):
        index = int(slider.val)
        # Update the color of the points using the selected index
        color_values = [color[index] for color in color_data]
        sc.set_array(np.array(color_values))
        sc.set_clim(vmin=0, vmax=max_value)
        # Update the edge colors based on "peopleList" associated with each edge
        for i, edge in enumerate(edges):
            people_list = edges[edge]["peopleList"]
            edge_lines[i].set_color(cmap(people_list[index] / max_value))

    slider.on_changed(update)

    # # Function to animate the slider
    # def animate_slider(frame):
    #     slider.set_val(frame)
    #     update(frame)

    # # Create an animation that moves the slider back and forth
    # ani = FuncAnimation(fig, animate_slider, frames=np.arange(0, 841, 1), repeat=True, interval=100)

    # # Save the animation as a GIF
    # ani.save("heatmap_animation.gif", writer="pillow", fps=120)

    plt.show()

def guest_vis(config):
    f = open(config)
    satisfactions = json.load(f)

    target_length = len(satisfactions["1"])
    # Iterate through the dictionary values and modify the lists
    for key, value in satisfactions.items():
        # Calculate the number of zeros to prepend
        zeros_to_prepend = target_length - len(value)
        
        if zeros_to_prepend > 0:
            # Prepend the necessary number of zeros to make the list the same length
            satisfactions[key] = [0] * zeros_to_prepend + value

   # Extract all satisfaction values and find the overall min and max
    all_satisfactions = np.concatenate(list(satisfactions.values()))
    min_satisfaction = all_satisfactions.min()
    max_satisfaction = all_satisfactions.max()

    # Convert the satisfaction data to a NumPy array
    satisfaction_data = np.array(list(satisfactions.values()))

    # Initialize the index for the slider
    selected_index = 0

    # Function to update the histogram based on the selected index
    def update_histogram(val, slider):
        global selected_index
        selected_index = int(slider.val)
        
        # Count the occurrences of each satisfaction value
        values = satisfaction_data[:, selected_index]
        unique_values, counts = np.unique(values, return_counts=True)
        total_count = len(values)
        percentages = (counts / total_count) * 100

        ax.clear()
        ax.bar(unique_values, percentages, width=1)
        ax.set_xlabel("Satisfaction Value")
        ax.set_ylabel("Percentage")
        ax.set_xlim(min_satisfaction, max_satisfaction)
        ax.set_ylim(0, 100)
        fig.canvas.draw()

    fig, ax = plt.subplots()
    plt.subplots_adjust(bottom=0.25)

    # Create a slider for selecting the index
    slider_ax = plt.axes([0.25, 0.1, 0.65, 0.03], facecolor='lightgoldenrodyellow')
    slider = Slider(slider_ax, 'Select Index', 0, satisfaction_data.shape[1] - 1, valinit=selected_index, valstep=1)

    slider.on_changed(lambda val: update_histogram(val, slider))

    update_histogram(0, slider)  # Initial plot

    plt.show()

def box_plot(config):
    f = open(config)
    satisfactions = json.load(f)

    data = [val[-1] for val in satisfactions.values()]

    q1 = np.percentile(data, 25)  # 1st quartile
    q2 = np.percentile(data, 50)  # 2nd quartile (median)
    q3 = np.percentile(data, 75)  # 3rd quartile
    min_value = np.min(data)
    max_value = np.max(data)

    iqr = q3 - q1

    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    outliers_below = [x for x in data if x < lower_bound]
    outliers_above = [x for x in data if x > upper_bound]

    print(f"[{len(outliers_below)}, {lower_bound}, {q1}, {q2}, {q3}, {upper_bound}, {len(outliers_above)}]")

    plt.boxplot(data, vert=False)  # Flip the axes
    plt.title("Box and Whisker Plot")
    plt.xlabel("Satisfaction")
    plt.show()

def all_outputs(config):
    zip_file = config + ".zip"
    with ZipFile(zip_file, 'r') as zObject: 
        zObject.extractall(path=config) 
    zObject.close() 

    guest_json = config + "/Guest.json"
    graph_json = config + "/Graph.json"
    party_json = config + "/Party.json"
    graph_vis(graph_json)
    guest_vis(guest_json)
    box_plot(guest_json)
    party_vis(party_json)

    shutil.rmtree(config)


def party_vis(config):
    f = open(config)
    parties = json.load(f)
    num_rides_list = []
    walk_list = []
    wait_list = []

    for party, value in parties.items():
        # print(f"This party rode {len(value['rides'])} rides, waited for {value['wait']} minutes, walked for {value['walk']} minutes, and has {value['num_guest']} guests")
        num_rides_list.append(len(value["rides"]))
        walk_list.append(value["walk"])
        wait_list.append(value["wait"])

    plt.subplot(2, 2, 1)  
    min_value = min(num_rides_list)
    max_value = max(num_rides_list)
    value_range = range(min_value, max_value + 1)
    value_counts = [num_rides_list.count(value) for value in value_range]  
    plt.bar(value_range, value_counts)
    # Add labels and title
    plt.xlabel("Num of Rides")
    plt.ylabel("Num of Parties")
    plt.title("Number of Rides for All Parties")


    plt.subplot(2, 2, 2)  
    min_value = min(walk_list)
    max_value = max(walk_list)
    value_range = range(min_value, max_value + 1)
    value_counts = [walk_list.count(value) for value in value_range]  
    plt.bar(value_range, value_counts)
    # Add labels and title
    plt.xlabel("Walking Time (min)")
    plt.ylabel("Num of Parties")
    plt.title("Walking Time (min) for All Parties")

    plt.subplot(2, 2, 3)  
    min_value = min(wait_list)
    max_value = max(wait_list)
    value_range = range(min_value, max_value + 1)
    value_counts = [wait_list.count(value) for value in value_range]  
    plt.bar(value_range, value_counts)
    # Add labels and title
    plt.xlabel("Waiting Time (min)")
    plt.ylabel("Num of Parties")
    plt.title("Waiting Time (min) for All Parties")

    plt.subplots_adjust(hspace=0.3)
    # Show the plot
    plt.show()
    

# config = "Output/KBAI/11_09 15_42"
# all_outputs(config)
# config = "Output/Closest/11_06 18_01"
# all_outputs(config)
config = "Output/Random/11_16 11_21"
all_outputs(config)
