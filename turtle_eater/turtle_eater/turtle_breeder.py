import rclpy
from rclpy.node import Node

# Importing necessary message and service types
from turtlesim.srv import Spawn  
from turtlesim.msg import Pose
from my_msg_interfaces.msg import PoseName,PoseArray

# Importing math and random modules for calculations and random number generation
import math as m
import random

class TurtleBreeder(Node):
    def __init__(self):
        super().__init__('turtle_breeder_node')
        self.get_logger().info('turtle breeder node has started')

        # Creates a client for the /spawn service
        self.client_ = self.create_client(Spawn,'/spawn') 

        # Waits for the /spawn service to be available
        while not self.client_.wait_for_service(timeout_sec=1.0):                     
            self.get_logger().warn('/spawn service not available...')

            '''This loop waits for the service to become available, checking every second. If the service is not available, 
            it logs a warning message and holds the program until the service is ready. Once the service is available, 
            the loop exits, allowing the program to proceed with creating variables for creating publishers subscribers 
            and service calls and calls them.'''

        # Spawnned Turtle counter   
        self.turtle_no = 0    

        # Timer to periodically check turtle population                                                       
        self.timer = self.create_timer(0.5,self.trtl_popul_ctrl)  

        # Publisher to send locations of spawned turtles as PoseArray
        self.publisher = self.create_publisher(PoseArray, '/food', 10)  

        # Dictionary to hold subscriptions for spawned turtles
        self.subs = {}

        # Dictionary to hold latest poses of spawned turtles
        self.pose_dict = {}
        



#---------------------------------------------------------------------------------------------------------------------

    # Function to call the spawn service
    def spawn_service(self): 

        # Increments turtle counter for every spawn and unique naming
        self.turtle_no += 1

        # Prepares the request for spawning a new turtle at random location
        request = Spawn.Request()
        request.x = random.uniform(0.5,10.5)
        request.y = random.uniform(0.5,10.5)
        request.theta = random.uniform(-m.pi,m.pi)
        request.name = f'food_{self.turtle_no}' # Unique turtle names

        future = self.client_.call_async(request)
        future.add_done_callback(self.spawn_response_callback)    # Callback function to handle the response from the /spawn service
        
#-----------------------------------------------------------------------------------------------------------------------------------        
        
    # Callback for service response
    def spawn_response_callback(self, future):                 # Callback function to handle the response from the /spawn service
        response: Spawn.Response = future.result()

        if response is not None:

            self.get_logger().info(f'Spawned turtle: {response.name}')

            # Create subscription for the newly spawned turtle to track its pose
            self.Spawn_callback(f'food_{self.turtle_no}')


        else:
            self.get_logger().error('Failed to call service /spawn')

        return

#-----------------------------------------------------------------------------------------------------------------------------------

    def Spawn_callback(self, turtle_name):
        # Callback function to update the pose of a spawned turtle along with its name
        def callback(location: Pose, name=turtle_name):

            # Creating PoseName object message to store pose with turtle name
            p = PoseName()   
            p.linear.x = location.x
            p.linear.y = location.y
            p.linear.z = 0.0
            p.angular.x = 0.0
            p.angular.y = 0.0
            p.angular.z = location.theta
            p.name = name
            self.pose_dict[name] = p  # Store the latest pose in the dictionary with turtle name as key

        # Creates a Subscriber to the pose of every spawned turtle as an element of subs dictionary
        self.subs[turtle_name] = self.create_subscription(Pose,f'/{turtle_name}/pose',callback,10) 

        return
        
        '''As the PoseName object p requires the name of the turtle, simply creating a normal call back fuction
          for this subscriber will only give the pose data of the turtle but not the name of the turtle 
          because turtle publishes the data in turtlesim geometric msgs Pose() format which doesnt have name 
          data on it but the PoseName() format from my custom msgs uses name of the turtle to store the data 
          of each turtle corresponding to its name.So a callback function is created with two type specified 
          arguements: one (name) with default argument as the turtle_name being passed to the parent function 
          from the spawn service callback and the other is pose data from Pose() object.'''         

#--------------------------------------------------------------------------------------------------------------------------------------------------------
    
    # Function to extract names of spawned turtles
    def turtle_name_extract(self):  

        # Get list of all topics to identify spawned turtles
        turtles_topic = self.get_topic_names_and_types() 

        # Creates Empty List to hold names of spawned turtles
        turtle_name_lst = []

        for name,Type in turtles_topic:
            if name.startswith('/food_') and name.endswith('/cmd_vel'): # Identify spawned turtles by their command velocity topics
                turtle_name_lst.append(name.split('/')[1])  # Extract turtle name from topic string


        return turtle_name_lst

        '''This function retrieves all topic names and types in the ROS2 system using get_topic_names_and_types().
       It then iterates through the list of topics, checking for those that start with /food_ and end with 
       /cmd_vel, which are the topics associated with the spawned turtles' velocity commands. The turtle names 
       are extracted from these topic strings and returned as a list. This allows the node to dynamically 
       identify and manage the turtles it has spawned. 
       
       Why /cmd_vel?
       Each turtle in turtlesim has multiple topics associated with it, including /pose for its position and 
       /cmd_vel for its velocity commands. By checking for /cmd_vel topics, we can reliably identify all 
       spawned turtles, as each turtle will have its own unique /cmd_vel topic.
       
       If we use /pose instead of /cmd_vel, the problem arises when you try to extract only the alive turtles' 
       names. When a turtle is killed, its /pose topic is not removed from the ROS2 system. Therefore, if we 
       check for /pose topics, we might end up including names of turtles that have been killed, leading to 
       inaccuracies in managing the turtle population. On the other hand, /cmd_vel topics are only present for 
       active turtles. When a turtle is killed, its /cmd_vel topic is removed, allowing us to accurately 
       identify only the alive turtles. This ensures that our turtle population management logic remains 
       correct and up-to-date.'''
    

#-----------------------------------------------------------------------------------------------------------------------------------

    # Function to control turtle population
    def trtl_popul_ctrl(self): 

        # Retrieves names of all currently alive turtles
        turtle_name = self.turtle_name_extract()  

        # Creates subscriptions for any new turtles that do not have existing subscriptions
        for i in range(len(turtle_name)):
            if turtle_name[i] not in self.subs:
                self.Pose_callback(turtle_name[i])

        # Spawns new turtles if total alive turtles are less than 6
        if len(turtle_name)<6:
             self.spawn_service()

        # Publishes the poses of all alive turtles
        self.pose_array_publisher()  

        return

    ''' this function first retrieves the names of all currently alive turtles using turtle_name_extract().
      It then checks if there are any already existing turtles that do not have a corresponding subscription in
      subs dictionary and creates subscriptions for them using Spawn_callback(). If the total number of alive 
      turtles is less than 6, it calls spawn_service() to spawn new turtles. Finally, it calls pose_array_publisher()
      to publish the current poses of all alive turtles. This ensures that the turtle population is maintained 
      at a minimum of 6 and that their poses are regularly updated and published.
      
      It was intentionally not built with while loop and instead with if clause so that it prevents multiple blocking 
      spawn statements. If the turtles is less than 6 it will spawn one turtle per spin and add its data to the
      list in the next spin and spawns next turtle'''
#-----------------------------------------------------------------------------------------------------------------------------------

    # Function to publish pose array of alive turtles
    def pose_array_publisher(self):  
        
        # Get names of currently alive turtles
        turtle_name = self.turtle_name_extract()

        # Create PoseArray message object to hold poses of alive turtles
        posearray = PoseArray()

        # Get list of keys in pose_dict to check for dead turtles
        lst = list(self.pose_dict.keys())

        # Deletes the dead turtle food s pose data from dictionary to prevent its pulishing  
        for name in lst:     
            if name not in turtle_name:
                del self.pose_dict[name]

        # Logs the names of currently alive turtles
        self.get_logger().info(f'Turtles alive: {list(self.pose_dict.keys())}')   


        # Appends poses of alive turtles dictionary key-value to PoseArray message
        for name in self.pose_dict:
            posearray.poses.append(self.pose_dict[name]) # Append each turtle's pose to the PoseArray


        # Publishes the PoseArray message containing poses of all alive turtles
        self.publisher.publish(posearray)

        return



             
        

def main(args=None):
    rclpy.init(args=args)
    node = TurtleBreeder()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()