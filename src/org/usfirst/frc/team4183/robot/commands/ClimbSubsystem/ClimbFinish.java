package org.usfirst.frc.team4183.robot.commands.ClimbSubsystem;

import org.usfirst.frc.team4183.robot.Robot;

import edu.wpi.first.wpilibj.command.Command;

/**
 *
 */
public class ClimbFinish extends Command {

    public ClimbFinish() {
        requires(Robot.climbSubsystem);
    }

    // We are so done...
    
    // Called just before this Command runs the first time
    protected void initialize() {
    	Robot.climbSubsystem.off();
    }

    // Called repeatedly when this Command is scheduled to run
    protected void execute() {
    	Robot.climbSubsystem.off();
    }

    // Make this return true when this Command no longer needs to run execute()
    protected boolean isFinished() {
    	Robot.climbSubsystem.off();
        return false;
    }

    // Called once after isFinished returns true
    protected void end() {
    	Robot.climbSubsystem.off();
    }

    // Called when another command which requires one or more of the same
    // subsystems is scheduled to run
    protected void interrupted() {
    	end();
    }
}
