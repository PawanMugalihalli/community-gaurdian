import logging
import requests
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

logger = logging.getLogger(__name__)

API_BASE = "http://localhost:8000/api"


def _build_incident_stats(incidents):
    return {
        "high_severity_count": sum(1 for i in incidents if i.get("severity", 0) >= 4),
        "ai_enriched_count":   sum(1 for i in incidents if i.get("ai_enriched")),
    }


@login_required
def feed_view(request):
    user = request.user

    # if profile_id is in query params → personalised mode
    # otherwise → public mode, use whatever filters are passed
    personalised = "profile_id" in request.GET

    params = {}
    if personalised:
        params["profile_id"] = user.id

    for key in ("location", "category", "severity", "search"):
        val = request.GET.get(key)
        if val:
            params[key] = val

    incidents = []
    try:
        r = requests.get(f"{API_BASE}/incidents/", params=params, timeout=5)
        if r.status_code == 200:
            incidents = r.json()
        else:
            messages.error(request, "Could not load incidents. Please try again.")
    except Exception as e:
        logger.error(f"Feed fetch error: {e}")
        messages.error(request, "Service temporarily unavailable.")

    stats = _build_incident_stats(incidents)

    return render(request, "incidents/feed.html", {
        "incidents":           incidents,
        "profile":             user,
        "personalised":        personalised,
        "high_severity_count": stats["high_severity_count"],
        "ai_enriched_count":   stats["ai_enriched_count"],
    })


@login_required
def profile_view(request):
    user = request.user

    if request.method == "POST":
        name     = request.POST.get("name", "").strip()
        location = request.POST.get("location", "").strip()
        concerns = request.POST.getlist("concerns")

        if not name or not location:
            messages.error(request, "Name and location are required.")
            return render(request, "incidents/profile.html", {
                "profile":           user,
                "selected_concerns": concerns,
                "edit_mode":         True,
            })

        try:
            user.name     = name
            user.location = location
            user.concerns = concerns
            user.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("/profile/")
        except Exception as e:
            logger.error(f"Profile update error: {e}")
            messages.error(request, "Could not update profile. Please try again.")

    return render(request, "incidents/profile.html", {
        "profile":           user,
        "selected_concerns": user.concerns,
        "edit_mode":         request.GET.get("edit") == "1",
    })


@login_required
def report_view(request):
    user = request.user

    if request.method == "POST":
        title       = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        location    = request.POST.get("location", "").strip()
        source      = request.POST.get("source", "user_report")

        errors = []
        if len(title) < 5:
            errors.append("Title must be at least 5 characters.")
        if len(description) < 10:
            errors.append("Description must be at least 10 characters.")
        if len(location) < 3:
            errors.append("Location must be at least 3 characters.")

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, "incidents/report.html", {
                "profile":          user,
                "profile_location": user.location,
                "form_data":        request.POST,
            })

        payload = {
            "title":       title,
            "description": description,
            "location":    location,
            "source":      source,
        }

        try:
            r = requests.post(f"{API_BASE}/incidents/", json=payload, timeout=5)
            if r.status_code == 201:
                messages.success(
                    request,
                    "Incident submitted. It will appear in the feed once processed (within 5 minutes)."
                )
                return redirect("feed")
            else:
                messages.error(request, f"Could not submit: {r.json()}")
        except Exception as e:
            logger.error(f"Report submit error: {e}")
            messages.error(request, "Service error. Please try again.")

        return render(request, "incidents/report.html", {
            "profile":          user,
            "profile_location": user.location,
            "form_data":        request.POST,
        })

    return render(request, "incidents/report.html", {
        "profile":          user,
        "profile_location": user.location,
        "form_data":        {},
    })