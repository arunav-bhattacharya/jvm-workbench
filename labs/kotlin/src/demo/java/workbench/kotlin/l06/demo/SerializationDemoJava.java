package workbench.kotlin.l06.demo;

import kotlinx.serialization.json.Json;

/**
 * Java twin of SerializationDemo.kt. The plugin's output is ordinary bytecode, so Java can use it:
 * Queued.Companion.serializer() returns the generated KSerializer, and Json.Default does the rest.
 * Java code normally uses a reflection-based JSON library instead; this shows what the plugin generated.
 */
public class SerializationDemoJava {
    public static void main(String[] args) {
        Queued q = new Queued("job-2", 1, "A4");
        String text = Json.Default.encodeToString(Queued.Companion.serializer(), q);
        System.out.println("Java, static type Queued: " + text);
        Queued back = Json.Default.decodeFromString(Queued.Companion.serializer(), text);
        System.out.println("decoded: " + back + ", equal: " + back.equals(q));
        System.out.println("generated serializer: " + Queued.Companion.serializer().getClass().getName());
    }
}
