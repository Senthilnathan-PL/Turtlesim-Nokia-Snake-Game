import rclpy
from rclpy.node import Node

# Importing necessary message and service types
from geometry_msgs.msg import Twist
from turtlesim.msg import Pose
from turtlesim.srv import Spawn, Kill
from my_msg_interfaces.msg import PoseArray

# Importing math module for calculations
import math as m

class TurtleEater(Node):
    def __init__(self):
        super().__init__('turtle_eater_node')
        self.get_logger().info('turtle eater node has started')  

        # Initialize eater position variables
        self.Xc = 0.0   # Current x position of turtle eater 
        self.Yc = 0.0   # Current y position of turtle eater
        self.Oc = 0.0   # Current orientation of turtle eater

        # Initialize target food position variables
        self.Xg = 0.0   # Goal x position (food)
        self.Yg = 0.0   # Goal y position (food)
        self.Og = 0.0   # Goal orientation (food)

        # Initialize turtle eater functionalities (publishing, subscribing, killing)
        self.turte_eater()

    def turte_eater(self):
        #giving velocity commands to turtle1
        self.publisher = self.create_publisher(Twist, 'turtle1/cmd_vel', 10)

        #subscribing to turtle1's position
        self.subscriber2 = self.create_subscription(Pose, '/turtle1/pose', self.turtle1_pose_callback, 10)

        #subscribing to food's positions 
        self.subscriber = self.create_subscription(PoseArray, '/food', self.subs_callback, 10)

        #kill eaten turtles
        self.client_kill = self.create_client(Kill,'/kill')

        #kill flag to prevent multiple kill requests in each navigation cycle (each spin)
        self.is_killing = True

#----------------------------------------------------------------------------------------------------------------------------------
    # Callback function to update turtle eater's pose
    def turtle1_pose_callback(self, msg: Pose):

        # Update current position and orientation of turtle eater
        self.turtle1_pose = msg
        self.Xc = msg.x
        self.Yc = msg.y
        self.Oc = msg.theta
        return
    
#----------------------------------------------------------------------------------------------------------------------------------

    # Callback function to process food positions
    def subs_callback(self, pose_array_msg: PoseArray):

        # Initializing minimum distance and target food
        min_distance = float('inf')
        self.target_food = None

        # Checks if any food is available
        if not pose_array_msg.poses:                        
            self.get_logger().warn("No food available.")
            return

        # Find the closest food item
        for pose in pose_array_msg.poses:
            
            distance = m.sqrt((pose.linear.x - self.Xc) ** 2 + (pose.linear.y - self.Yc) ** 2)
            if distance < min_distance:
                min_distance = distance
                self.target_food = pose

        
        # Update goal position and orientation to the closest food
        self.Xg = self.target_food.linear.x
        self.Yg = self.target_food.linear.y
        self.Og = self.target_food.angular.z

        # Navigate towards the target food
        self.navigate_to_food()
        return

#----------------------------------------------------------------------------------------------------------------------------------
    
    # Distance error calculation
    def dist_error(self):    # Distance error calculation
        del_x2 = (self.Xg - self.Xc)**2
        del_y2 = (self.Yg - self.Yc)**2
        err = m.sqrt(del_x2 + del_y2)
        return err

#----------------------------------------------------------------------------------------------------------------------------------
    
    # Angular error calculation
    def ang_error(self):

        del_x = (self.Xg - self.Xc)
        del_y = (self.Yg - self.Yc)

        # Uses arctangent2 to avoid division by zero
        err = (m.atan2(del_y,del_x)-self.Oc)   

        # Normalize angle to be within [-pi, pi]
        err = (err + (2*m.pi)) if err < -m.pi else err  
        err = (err - (2*m.pi)) if err > m.pi else err
        return err

#----------------------------------------------------------------------------------------------------------------------------------
    
    # Navigation towards food
    def navigate_to_food(self):

        # Check if there is a target food to navigate to
        if self.target_food:

            # Creates a Twist message object to control turtle eater's movement
            twist_msg = Twist()

            
            if abs(self.dist_error()) <= 0.2 and self.is_killing:
                # Check if the turtle eater is close enough to the food to "eat" it
                # Also checks if it is in killing state to avoid multiple kill requests


                # Stop the turtle eater's movementbefore killing the food
                twist_msg.linear.x = 0.0
                twist_msg.angular.z = 0.0     
                self.publisher.publish(twist_msg)  

                # Create and send kill request for the target food 
                kill_req = Kill.Request()
                kill_req.name = self.target_food.name
                kill_future = self.client_kill.call_async(kill_req)
                self.is_killing = False
                kill_future.add_done_callback(self.kill_cb)  # Callback for kill response


                
            else:
                # Move towards the food using proportional control
                # Linear velocity is proportional to distance error
                # Angular velocity is proportional to angular error
                # Accelerated motion
                # Adjusts behavior near boundaries

                if self.Xc>=10.0 or self.Xc<=1.0 or self.Yc>=10.0 or self.Yc<=1.0:
                    if abs(self.ang_error())>=0.01:
                        twist_msg.angular.z = 1.0 * self.ang_error()
                        twist_msg.linear.x = 0.0
                    else:
                        twist_msg.linear.x = 1.0 * self.dist_error()
                        twist_msg.angular.z = 2.0 * self.ang_error()
                else:   
                    twist_msg.linear.x = 1.0 * self.dist_error()
                    twist_msg.angular.z = 2.0 * self.ang_error()

                # Publishes the velocity commands    
                self.publisher.publish(twist_msg)
        return


 #----------------------------------------------------------------------------------------------------------------------------------


    # Callback function for kill service response   
    def kill_cb(self, future):

        # Process the result of the kill service call
        res = future.result()
        if res:

            # Logs successful eating of the food
            self.get_logger().info(f"Eaten {self.target_food.name}!!!")

            # Resets target food and kill flag for next navigation cycle
            self.target_food = None  
            self.is_killing = True

        else:

            # Logs failure to eat the food
            self.get_logger().info("Failed to eat the food.") 
        return    

        


def main(args=None):
    rclpy.init(args=args)
    node = TurtleEater()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()