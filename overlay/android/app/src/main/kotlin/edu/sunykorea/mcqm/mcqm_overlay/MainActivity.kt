package edu.sunykorea.mcqm.mcqm_overlay

import android.content.Context
import android.content.Intent
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.provider.Settings
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

// M0-a 스파이크: Wi-Fi RSSI 읽기, SCHEMA v1.1 action.code → Android 설정 패널 열기
class MainActivity : FlutterActivity() {
    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, "mcqm/device").setMethodCallHandler { call, result ->
            when (call.method) {
                "rssi" -> result.success(wifiRssi())
                "openPanel" -> {
                    val action = when (call.argument<String>("code")) {
                        "open_wifi_panel" -> Settings.Panel.ACTION_WIFI
                        "open_internet_panel" -> Settings.Panel.ACTION_INTERNET_CONNECTIVITY
                        else -> null
                    }
                    if (action == null) {
                        result.error("bad_code", "unknown action code", null)
                    } else {
                        startActivity(Intent(action).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
                        result.success(true)
                    }
                }
                else -> result.notImplemented()
            }
        }
    }

    // WifiManager.connectionInfo는 Android 13에서 위치 권한이 없으면 networkId가 가려진다(10/13 확인).
    // NetworkCapabilities.signalStrength(API 29+)는 위치 권한 없이 RSSI를 준다. VPN(PCAPdroid)이 켜져 있어도
    // 실제 Wi-Fi 네트워크를 찾도록 활성 네트워크가 아니라 전체 네트워크에서 Wi-Fi 전송을 고른다.
    private fun wifiRssi(): Int? {
        val cm = applicationContext.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        @Suppress("DEPRECATION")
        for (n in cm.allNetworks) {
            val caps = cm.getNetworkCapabilities(n) ?: continue
            if (caps.hasTransport(NetworkCapabilities.TRANSPORT_WIFI) &&
                caps.signalStrength != NetworkCapabilities.SIGNAL_STRENGTH_UNSPECIFIED
            ) return caps.signalStrength
        }
        return null
    }
}
