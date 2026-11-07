package workbench.startup.l03;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.io.InputStream;
import java.lang.reflect.Proxy;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.Set;

import static org.assertj.core.api.Assertions.assertThat;

/** Checks your hand-written reachability-metadata.json against schema v1.2.0 and against what the code does. */
class MetadataFileTest {
    static final String PATH = "META-INF/native-image/workbench/startup/reachability-metadata.json";

    // schema v1.2.0: top-level properties, and the properties a reflection entry may have
    static final Set<String> TOP_LEVEL = Set.of("comment", "reflection", "resources", "foreign");
    static final Set<String> ENTRY_KEYS = Set.of("reason", "condition", "type", "methods", "fields",
            "allDeclaredMethods", "allDeclaredFields", "allDeclaredConstructors", "allPublicMethods",
            "allPublicFields", "allPublicConstructors", "unsafeAllocated", "serializable", "jniAccessible");

    private Map<String, Object> doc;

    @SuppressWarnings("unchecked")
    @BeforeEach
    void readFile() throws Exception {
        try (InputStream in = getClass().getClassLoader().getResourceAsStream(PATH)) {
            assertThat(in).as("the file must be on the class path at " + PATH).isNotNull();
            doc = (Map<String, Object>) MiniJson.parse(new String(in.readAllBytes(), StandardCharsets.UTF_8));
        }
    }

    @SuppressWarnings("unchecked")
    private List<Map<String, Object>> reflection() {
        return (List<Map<String, Object>>) doc.getOrDefault("reflection", List.of());
    }

    @Test
    @DisplayName("uses only the top-level keys of schema v1.2.0 (no 'proxy', 'jni' or 'serialization' sections)")
    void topLevelKeys() {
        assertThat(TOP_LEVEL).containsAll(doc.keySet());
    }

    @Test
    @DisplayName("every reflection entry has a type and only schema fields; every method has name and parameterTypes")
    @SuppressWarnings("unchecked")
    void entriesFollowTheSchema() {
        for (Map<String, Object> entry : reflection()) {
            assertThat(entry).containsKey("type");
            assertThat(ENTRY_KEYS).containsAll(entry.keySet());
            Object type = entry.get("type");
            if (type instanceof Map<?, ?> t) {
                assertThat(Set.of("proxy", "lambda")).as("an object type is a proxy or a lambda").containsAll(
                        t.keySet().stream().map(String::valueOf).toList());
            } else {
                assertThat(type).isInstanceOf(String.class);
            }
            for (Map<String, Object> m : (List<Map<String, Object>>) entry.getOrDefault("methods", List.of())) {
                assertThat(m.keySet()).as("a method is exactly {name, parameterTypes}").containsExactlyInAnyOrder("name", "parameterTypes");
            }
        }
    }

    @Test
    @DisplayName("registers the constructor and the accessors EventDecoder calls on PaymentAuthorized")
    @SuppressWarnings("unchecked")
    void registersTheEventClass() throws Exception {
        // the code under test really works this way on the JVM
        Object event = EventDecoder.decode(PaymentAuthorized.class.getName(), "pay_81", "EUR", 1250L);
        assertThat(EventDecoder.describe(event)).containsEntry("amountMinor", 1250L);

        Map<String, Object> entry = reflection().stream()
                .filter(e -> PaymentAuthorized.class.getName().equals(e.get("type")))
                .findFirst().orElseThrow(() -> new AssertionError("no reflection entry with type " + PaymentAuthorized.class.getName()));
        List<Map<String, Object>> methods = (List<Map<String, Object>>) entry.getOrDefault("methods", List.of());
        assertThat(methods).contains(
                Map.of("name", "<init>", "parameterTypes", List.of("java.lang.String", "java.lang.String", "long")));
        for (String accessor : EventDecoder.ACCESSORS) {
            assertThat(methods).contains(Map.of("name", accessor, "parameterTypes", List.of()));
        }
    }

    @Test
    @DisplayName("registers the proxy IssuerClients creates, with its interfaces in the same order")
    @SuppressWarnings("unchecked")
    void registersTheProxy() {
        CardIssuerClient client = IssuerClients.connect("https://issuer.example");
        assertThat(Proxy.isProxyClass(client.getClass())).isTrue();
        List<String> actual = Arrays.stream(client.getClass().getInterfaces()).map(Class::getName).toList();

        List<List<String>> proxies = reflection().stream()
                .map(e -> e.get("type"))
                .filter(t -> t instanceof Map<?, ?> m && m.containsKey("proxy"))
                .map(t -> (List<String>) ((Map<String, Object>) t).get("proxy"))
                .toList();
        assertThat(proxies).as("a reflection entry whose type is {\"proxy\": " + actual + "}").contains(actual);
    }
}
