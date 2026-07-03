{{- define "zulip-linear-bot.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "zulip-linear-bot.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- printf "%s" $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{- define "zulip-linear-bot.labels" -}}
helm.sh/chart: {{ include "zulip-linear-bot.name" . }}
app.kubernetes.io/name: {{ include "zulip-linear-bot.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "zulip-linear-bot.selectorLabels" -}}
app.kubernetes.io/name: {{ include "zulip-linear-bot.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
