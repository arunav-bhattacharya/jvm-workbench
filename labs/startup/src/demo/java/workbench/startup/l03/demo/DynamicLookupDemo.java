package workbench.startup.l03.demo;

import java.lang.reflect.Method;

/**
 * Calls a static, no-argument method chosen at run time, by class name and method name.
 * On the JVM any class on the class path works. A native image can only do this for the
 * classes and methods listed in its reachability metadata, so the demo prints that entry too.
 */
public class DynamicLookupDemo {
    public static void main(String[] args) throws Exception {
        String className = args.length > 0 ? args[0] : "java.time.LocalDate";
        String methodName = args.length > 1 ? args[1] : "now";

        Class<?> type = Class.forName(className);          // a name from data: the analysis can't see it
        Method method = type.getMethod(methodName);
        System.out.println(className + "." + methodName + "() = " + method.invoke(null));

        System.out.println("A native image needs this in reachability-metadata.json:");
        System.out.printf("{ \"reflection\": [ { \"type\": \"%s\", \"methods\": [ { \"name\": \"%s\", \"parameterTypes\": [] } ] } ] }%n",
                type.getName(), method.getName());
    }
}
