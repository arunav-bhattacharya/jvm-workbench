package workbench.startup.l03.demo;

import java.time.Instant;
import java.util.Random;

/**
 * Static state computed in a class initializer. On the JVM it is computed again on every start.
 * In a native image built with build-time initialization (the Quarkus default), the initializer
 * runs once, inside the build, and every start of the binary sees the build's values.
 */
public class BuildTimeInitDemo {
    static final class InstanceInfo {
        static final Instant STARTED_AT = Instant.now();      // build-time init: the build's time, forever
        static final Random JITTER = new Random();           // build-time init: the native builder rejects it
    }

    public static void main(String[] args) {
        System.out.println("started at: " + InstanceInfo.STARTED_AT);
        System.out.println("retry jitter ms: " + InstanceInfo.JITTER.nextInt(250));
    }
}
