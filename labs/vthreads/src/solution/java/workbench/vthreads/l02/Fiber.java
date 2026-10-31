package workbench.vthreads.l02;

/**
 * A continuation written by hand. Each call to {@link #resume()} runs the task from where it
 * stopped last time until its next blocking point, then returns what it is waiting for.
 *
 * <p>A real virtual thread does not need this: the JDK saves its stack frames for it.
 * Here the fiber keeps its own "where was I" state in fields, like a Kotlin suspend function does.
 */
@FunctionalInterface
public interface Fiber {
    Step resume();
}
