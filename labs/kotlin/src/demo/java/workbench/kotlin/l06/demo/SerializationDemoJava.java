package workbench.kotlin.l06.demo;

import kotlinx.serialization.json.Json;

/**
 * Java twin of SerializationDemo.kt. The plugin's output is ordinary bytecode, so Java can use it:
 * Posted.Companion.serializer() returns the generated KSerializer, and Json.Default does the rest.
 * Java code normally uses Jackson instead; this shows what the plugin generated.
 */
public class SerializationDemoJava {
    public static void main(String[] args) {
        Posted p = new Posted("pay_2", 1L, "EUR");
        String text = Json.Default.encodeToString(Posted.Companion.serializer(), p);
        System.out.println("Java, static type Posted: " + text);
        Posted back = Json.Default.decodeFromString(Posted.Companion.serializer(), text);
        System.out.println("decoded: " + back + ", equal: " + back.equals(p));
        System.out.println("generated serializer: " + Posted.Companion.serializer().getClass().getName());
    }
}
