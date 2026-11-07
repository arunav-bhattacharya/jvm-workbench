package workbench.startup.l03.demo

/**
 * Calls a static, no-argument method chosen at run time, by class name and method name.
 * On the JVM any class on the class path works. A native image can only do this for the
 * classes and methods listed in its reachability metadata, so the demo prints that entry too.
 */
fun main(args: Array<String>) {
    val className = args.getOrElse(0) { "java.time.LocalDate" }
    val methodName = args.getOrElse(1) { "now" }

    val type = Class.forName(className)                // a name from data: the analysis can't see it
    val method = type.getMethod(methodName)
    println("$className.$methodName() = ${method.invoke(null)}")

    println("A native image needs this in reachability-metadata.json:")
    println("""{ "reflection": [ { "type": "${type.name}", "methods": [ { "name": "${method.name}", "parameterTypes": [] } ] } ] }""")
}
