#!/usr/bin python3

#Import Py tree ros 
import py_trees
import py_trees_ros

#Import Interface
from humanoid_interfaces.msg import Ball,Robot  
import std_msgs.msg as std_msgs
import py_trees.console as console



class Ball_Check_Success(py_trees.behaviour.Behaviour):
    '''
    Tree for checking Ball Success
    '''
    def __init__(
            self,
            name: str,
            topic_name: str="/behavior/ball_check_success", 

    ):
        super(Ball_Check_Success, self).__init__(name=name)

        self.ball_behavior = Ball()  # Declare Ball message
        self.topic_name = topic_name  


    def setup(self, **kwargs):
        '''
        Default setup function of py trees
        '''
        self.logger.debug("{}.setup()".format(self.qualified_name))
        try:
            self.node = kwargs['node']
        except KeyError as e:
            error_message = "didn't find 'node' in setup's kwargs [{}][{}]".format(self.qualified_name)
            raise KeyError(error_message) from e  # 'direct cause' traceability

        self.publisher = self.node.create_publisher(
            msg_type=std_msgs.String,
            topic=self.topic_name,
            qos_profile=py_trees_ros.utilities.qos_profile_latched()
        )
        # self.feedback_message = "publisher created"

    def update(self) -> py_trees.common.Status:
        '''
        Updating data to Tree by publishing topic  and Returning status as Running to keep checking Ball Detection
        '''
        self.logger.debug("%s.update()" % self.__class__.__name__)
        self.publisher.publish(std_msgs.String(data=str(self.ball_behavior.is_detected)))
        # self.feedback_message = "flashing {0}".format(self.colour)
        return py_trees.common.Status.RUNNING

    def terminate(self, new_status: py_trees.common.Status):
        '''
        Default terminate function of py trees
        '''
        self.logger.debug(
            "{}.terminate({})".format(
                self.qualified_name,
                "{}->{}".format(self.status, new_status) if self.status != new_status else "{}".format(new_status)
            )
        )
        self.publisher.publish(std_msgs.String(data=""))
        self.feedback_message = "cleared"


class Finding_Ball(py_trees.behaviour.Behaviour):
    '''
    Tree for finding ball
    '''
    def __init__(self,name: str,topic_name: str="/behavior/finding_ball",):
        super(Finding_Ball, self).__init__(name=name)
        self.ball_behavior = Ball()
        self.topic_name = topic_name
        self.subscribe_topic = 'ball/detection'   #get bool of ball detection via this topic (should be published from camera node)
        
    def callback_msg(self,msg):
        self.msg_callback = msg.is_detected
        return  self.msg_callback

    def setup(self, **kwargs):
        '''
        Default setup
        '''
        self.logger.debug("{}.setup()".format(self.qualified_name))
        try:
            self.node = kwargs['node']
        except KeyError as e:
            error_message = "didn't find 'node' in setup's kwargs [{}][{}]".format(self.qualified_name)
            raise KeyError(error_message) from e  # 'direct cause' traceability
        # Create Publisher data to behavior's topic
        self.publisher = self.node.create_publisher(
            msg_type=std_msgs.String,  #Using String as msg type
            topic=self.topic_name,
            qos_profile=py_trees_ros.utilities.qos_profile_latched()
        )

        # Create Subscriber to subscribe data of this topic
        self.subscriber = self.node.create_subscription(msg_type=Ball,topic=self.subscribe_topic ,callback =self.callback_msg,qos_profile=1)

    
    def update(self) -> py_trees.common.Status:
        self.logger.debug("%s.update()" % self.__class__.__name__)

        #Conditioning to update tree status
        try:
            ball_detected = self.msg_callback   # try to subscribe msg
        except:
            ball_detected = False
        if not ball_detected:   
            return py_trees.common.Status.RUNNING   # Keep waiting for ball detection
        else:
            return py_trees.common.Status.SUCCESS  # if ball is deteced return Success to do next task

    def terminate(self, new_status: py_trees.common.Status):
        '''
        Default terminate funtion
        '''
        self.logger.debug(
            "{}.terminate({})".format(
                self.qualified_name,
                "{}->{}".format(self.status, new_status) if self.status != new_status else "{}".format(new_status)
            )
        )
        self.publisher.publish(std_msgs.String(data=""))
        self.feedback_message = "cleared"


class Nearest_Robot(py_trees.behaviour.Behaviour):
    '''
    Behavior for checking which robot is neareast
    '''
    def __init__(
            self,
            name: str,
            threshold_distance : float,
            topic_name: str="/behavior/nearest_robot",):
        super(Nearest_Robot, self).__init__(name=name)
        self.robot = Robot()
        self.topic_name = topic_name
        self.threshold_distance = threshold_distance
        self.subscribe_topic ='robot/nearest_id'   #Subscribe data as ID of robot which nearest to the ball
        
    def callback_msg(self,msg):
        self.msg_callback = msg
        return  self.msg_callback


    def setup(self, **kwargs):
        '''
        Default Setup
        '''
        self.logger.debug("{}.setup()".format(self.qualified_name))
        try:
            self.node = kwargs['node']
        except KeyError as e:
            error_message = "didn't find 'node' in setup's kwargs [{}][{}]".format(self.qualified_name)
            raise KeyError(error_message) from e  # 'direct cause' traceability
        
        #Create Pubsliher and Subscriber to this behavior via topics name

        self.publisher = self.node.create_publisher(
            msg_type=Robot,
            topic=self.topic_name,
            qos_profile=py_trees_ros.utilities.qos_profile_latched()
        )
        self.subscriber = self.node.create_subscription(msg_type=Robot,topic=self.subscribe_topic ,callback =self.callback_msg,qos_profile=1)
        
        
    def update(self) -> py_trees.common.Status:
        self.logger.debug("%s.update()" % self.__class__.__name__)
        try:
            if self.msg_callback!=0:     # If the ID of robot is subscribed which is not 0 (0 is None)
                msg = Robot()
                console.info(f'The Robot Id which nearest to the ball is : { self.msg_callback.id_robot_nearest_ball} ')
                self.publish_bhv = msg
                self.publish_bhv.id_robot_nearest_ball = self.msg_callback.id_robot_nearest_ball    # Update ID robot
                self.publish_bhv.distance_robot_ball = self.msg_callback.distance_robot_ball       # Update a distance between nearest robot and a ball
                self.publisher.publish(self.publish_bhv)
                if self.msg_callback.distance_robot_ball <= self.threshold_distance:    # Conditioning Action of robot (checking via threshold in main root)
                    console.info('KICK')   # Example of Robot's action
                else: 
                    console.info('WALK')    # Example of Robot's action
                return py_trees.common.Status.SUCCESS
            else:
                return py_trees.common.Status.RUNNING    # IF ID of robot is 0 -> Keep running tree
        except:
                return py_trees.common.Status.RUNNING

    def terminate(self, new_status: py_trees.common.Status):
        '''
        Default Terminate
        '''
        self.logger.debug( "{}.terminate({})".format(self.qualified_name, "{}->{}".format(self.status, new_status) if self.status != new_status else "{}".format(new_status)) )
        self.feedback_message = "cleared"
    
