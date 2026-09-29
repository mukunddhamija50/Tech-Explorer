import com.sun.net.httpserver.Headers;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;

import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;



public class index {









    public static void main(String[] args) throws Exception {

        HttpServer server = HttpServer.create(
                new InetSocketAddress(8080),
                0
        );


        // =====================================================
        // HELLO API
        // =====================================================

        server.createContext("/api/hello", exchange -> {

            if (handleOptions(exchange)) {
                return;
            }

            String response =
                    "Hello from Java backend";

            sendResponse(
                    exchange,
                    response
            );

        });


        // =====================================================
        // SKILLS API
        // =====================================================

        server.createContext("/api/skills", exchange -> {

            if (handleOptions(exchange)) {
                return;
            }

            String response =
                    "["
                    + "{"
                    + "\"name\":\"Python + SQL\","
                    + "\"demand\":\"High\","
                    + "\"level\":\"Advanced\""
                    + "},"

                    + "{"
                    + "\"name\":\"Java Full Stack\","
                    + "\"demand\":\"High\","
                    + "\"level\":\"Intermediate\""
                    + "},"

                    + "{"
                    + "\"name\":\"Cloud\","
                    + "\"demand\":\"High\","
                    + "\"level\":\"Intermediate\""
                    + "},"

                    + "{"
                    + "\"name\":\"Applied Data Analytics\","
                    + "\"demand\":\"High\","
                    + "\"level\":\"Advanced\""
                    + "},"

                    + "{"
                    + "\"name\":\"Generative AI\","
                    + "\"demand\":\"High\","
                    + "\"level\":\"Intermediate\""
                    + "},"

                    + "{"
                    + "\"name\":\"Machine Learning & Generative AI\","
                    + "\"demand\":\"High\","
                    + "\"level\":\"Advanced\""
                    + "}"

                    + "]";


            sendResponse(
                    exchange,
                    response
            );

        });


        // =====================================================
        // JOBS API
        // =====================================================

        server.createContext("/api/jobs", exchange -> {

            if (handleOptions(exchange)) {
                return;
            }

            String response =
                    "["
                    + "{"
                    + "\"title\":\"Full Stack Developer\","
                    + "\"skills\":\"Java, Spring Boot, SQL\""
                    + "},"

                    + "{"
                    + "\"title\":\"Python Developer\","
                    + "\"skills\":\"Python, SQL, FastAPI\""
                    + "},"

                    + "{"
                    + "\"title\":\"Data Analyst\","
                    + "\"skills\":\"Python, SQL, Database Management\""
                    + "},"

                    + "{"
                    + "\"title\":\"Cyber Security\","
                    + "\"skills\":\"Networking,Operating Systems,Linux\""
                    + "},"

                    + "{"
                    + "\"title\":\"AI & ML Engineer\","
                    + "\"skills\":\"Python, AI, Machine Learning, SQL, LLM, API\""
                    + "},"

                    + "{"
                    + "\"title\":\"Cloud Engineer\","
                    + "\"skills\":\"Cloud, Linux, AWS, Networking\""
                    + "}"

                    + "]";


            sendResponse(
                    exchange,
                    response
            );

        });


        // =====================================================
        // PROGRAMS API
        // =====================================================

        server.createContext("/api/programs", exchange -> {

            if (handleOptions(exchange)) {
                return;
            }

            String response =
                    "["
                    + "{"
                    + "\"name\":\"Full Stack Java Development Bootcamp\","
                    + "\"skill\":\"Java,Java Spring Boot,Programming Languages\","
                    + "\"duration\":\"6 Months\""
                    + "},"

                    + "{"
                    + "\"name\":\"Python Programming & Database Management\","
                    + "\"skill\":\"Python,SQL\","
                    + "\"duration\":\"4 Months\""
                    + "},"

                    

                    + "{"
                    + "\"name\":\"Cloud Engineering with AWS & Azure\","
                    + "\"skill\":\"Cloud,AWS,Azure\","
                    + "\"duration\":\"5 Months\""
                    + "},"

                    + "{"
                    + "\"name\":\"Applied Data Analytics\","
                    + "\"skill\":\"Data Analytics,SQL,Excel\","
                    + "\"duration\":\"5 Months\""
                    + "},"

                    + "{"
                    + "\"name\":\"Machine Learning & Generative AI Specialization\","
                    + "\"skill\":\"Machine Learning,LLMs,Generative AI\","
                    + "\"duration\":\"5 Months\""
                    + "},"

                    + "{"
                    + "\"name\":\"Cyber Security Analyst Track\","
                    + "\"skill\":\"Networking,Operating Systems,Web & Application Security,Network Security\","
                    + "\"duration\":\"10 Months\""
                    + "}"

                    

                   

                    + "]";


            sendResponse(
                    exchange,
                    response
            );

        });


        // =====================================================
        // START SERVER
        // =====================================================

        server.start();


        System.out.println(
                "================================="
        );

        System.out.println(
                "Tech Explorer Java Backend Started!"
        );

        System.out.println(
                "Server running at:"
        );

        System.out.println(
                "http://localhost:8080"
        );

        System.out.println(
                "================================="
        );

    }


    // =====================================================
    // HANDLE OPTIONS / CORS
    // =====================================================

    private static boolean handleOptions(
            HttpExchange exchange
    ) throws IOException {

        if (
                exchange
                        .getRequestMethod()
                        .equalsIgnoreCase("OPTIONS")
        ) {

            Headers headers =
                    exchange.getResponseHeaders();


            headers.set(
                    "Access-Control-Allow-Origin",
                    "*"
            );


            headers.set(
                    "Access-Control-Allow-Methods",
                    "GET, OPTIONS"
            );


            headers.set(
                    "Access-Control-Allow-Headers",
                    "Content-Type"
            );


            exchange.sendResponseHeaders(
                    204,
                    -1
            );


            exchange.close();


            return true;

        }


        return false;

    }


    // =====================================================
    // SEND RESPONSE
    // =====================================================

    private static void sendResponse(
            HttpExchange exchange,
            String response
    ) throws IOException {

        Headers headers =
                exchange.getResponseHeaders();


        headers.set(
                "Access-Control-Allow-Origin",
                "*"
        );


        headers.set(
                "Access-Control-Allow-Methods",
                "GET, OPTIONS"
        );


        headers.set(
                "Access-Control-Allow-Headers",
                "Content-Type"
        );


        headers.set(
                "Content-Type",
                "application/json; charset=UTF-8"
        );


        byte[] bytes =
                response.getBytes(
                        StandardCharsets.UTF_8
                );


        exchange.sendResponseHeaders(
                200,
                bytes.length
        );


        try (
                OutputStream output =
                        exchange.getResponseBody()
        ) {

            output.write(bytes);

        }

    }

}