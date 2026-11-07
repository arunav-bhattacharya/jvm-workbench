package workbench.startup.l03;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.io.Closeable;
import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class MetadataWriterTest {
    private static final String EVENT = "workbench.startup.l03.PaymentAuthorized";

    @Test
    @DisplayName("a constructor is <init> and parameter types are fully qualified, primitives by name")
    void constructorEntry() throws Exception {
        Map<String, Object> entry = MetadataWriter.reflection(PaymentAuthorized.class,
                PaymentAuthorized.class.getConstructor(String.class, String.class, long.class));
        assertThat(entry).isEqualTo(Map.of(
                "type", EVENT,
                "methods", List.of(Map.of("name", "<init>",
                        "parameterTypes", List.of("java.lang.String", "java.lang.String", "long")))));
    }

    @Test
    @DisplayName("methods are listed by name, in argument order, with empty parameterTypes when they take none")
    void methodEntries() throws Exception {
        Map<String, Object> entry = MetadataWriter.reflection(PaymentAuthorized.class,
                PaymentAuthorized.class.getMethod("paymentId"), PaymentAuthorized.class.getMethod("currency"));
        assertThat(entry.get("methods")).isEqualTo(List.of(
                Map.of("name", "paymentId", "parameterTypes", List.of()),
                Map.of("name", "currency", "parameterTypes", List.of())));
    }

    @Test
    @DisplayName("a member declared by another class is rejected")
    void foreignMemberRejected() {
        assertThatThrownBy(() -> MetadataWriter.reflection(PaymentAuthorized.class, String.class.getMethod("length")))
                .isInstanceOf(IllegalArgumentException.class);
    }

    @Test
    @DisplayName("a proxy entry keeps the interfaces in the order given")
    void proxyOrder() {
        assertThat(MetadataWriter.proxy(CardIssuerClient.class, AutoCloseable.class)).isEqualTo(
                Map.of("type", Map.of("proxy", List.of("workbench.startup.l03.CardIssuerClient", "java.lang.AutoCloseable"))));
        assertThat(MetadataWriter.proxy(AutoCloseable.class, CardIssuerClient.class)).isEqualTo(
                Map.of("type", Map.of("proxy", List.of("java.lang.AutoCloseable", "workbench.startup.l03.CardIssuerClient"))));
    }

    @Test
    @DisplayName("a proxy entry rejects classes and repeated interfaces, like java.lang.reflect.Proxy")
    void proxyRules() {
        assertThatThrownBy(() -> MetadataWriter.proxy(CardIssuerClient.class, PaymentAuthorized.class))
                .isInstanceOf(IllegalArgumentException.class);
        assertThatThrownBy(() -> MetadataWriter.proxy(Closeable.class, Closeable.class))
                .isInstanceOf(IllegalArgumentException.class);
    }

    @Test
    @DisplayName("a document written by toJson parses back to the same entries")
    void jsonRoundTrip() throws Exception {
        String json = MetadataWriter.toJson(MetadataWriter.document(List.of(
                MetadataWriter.proxy(CardIssuerClient.class, AutoCloseable.class))));
        Object parsed = MiniJson.parse(json);
        assertThat(parsed).isEqualTo(Map.of("reflection", List.of(
                Map.of("type", Map.of("proxy", List.of("workbench.startup.l03.CardIssuerClient", "java.lang.AutoCloseable"))))));
    }
}
