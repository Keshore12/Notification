'use strict';

const pushButton = document.querySelector('.js-push-btn');

let isSubscribed = false;
let swRegistration = null;


function urlB64ToUint8Array(base64String) {
	const padding = '='.repeat((4 - base64String.length % 4) % 4);
	const base64 = (base64String + padding)
		.replace(/\-/g, '+')
		.replace(/_/g, '/');

	const rawData = window.atob(base64);
	const outputArray = new Uint8Array(rawData.length);

	for (let i = 0; i < rawData.length; ++i) {
		outputArray[i] = rawData.charCodeAt(i);
	}
	return outputArray;
}

function updateBtn() {
	if (Notification.permission === 'denied') {
		pushButton.textContent = 'Push Messaging Blocked.';
		pushButton.disabled = true;
		updateSubscriptionOnServer(null);
		return;
	}

	if (isSubscribed) {
		pushButton.textContent = 'Disable Push Messaging';
	} else {
		pushButton.textContent = 'Enable Push Messaging';
	}

	pushButton.disabled = false;
}

function updateSubscriptionOnServer(subscription, industry_name) {
    var msg = {'sub_token': subscription, 'industry': industry_name}
	$.ajax({
		type: "POST",
		url: "/api/v1/subscribers/",
		contentType: 'application/json; charset=utf-8',
		dataType:'json',
		data: JSON.stringify(msg),
		success: function( data ){
			console.log("success",data);
    },
    error: function( jqXhr, textStatus, errorThrown ){
        console.log("error",errorThrown);
    }
	});
}

function subscribeUser(industry_name) {
	const applicationServerPublicKey = localStorage.getItem('applicationServerPublicKey');
	const applicationServerKey = urlB64ToUint8Array(applicationServerPublicKey);
	swRegistration.pushManager.subscribe({
			userVisibleOnly: true,
			applicationServerKey: applicationServerKey
		})
		.then(function(subscription) {
            console.log('User is subscribed.');
            console.log(subscription);

			updateSubscriptionOnServer(subscription, industry_name);
			localStorage.setItem('sub_token',JSON.stringify(subscription));
			isSubscribed = true;
			updateBtn();
		})
		.catch(function(err) {
			console.log('Failed to subscribe the user: ', err);
			updateBtn();
		});
}

function unsubscribeUser(industry_name) {
	swRegistration.pushManager.getSubscription()
		.then(function(subscription) {
			if (subscription) {
				return subscription.unsubscribe();
			}
		})
		.catch(function(error) {
			console.log('Error unsubscribing', error);
		})
		.then(function() {
			//updateSubscriptionOnServer(null, industry_name);

			console.log('User is unsubscribed.');
			isSubscribed = false;

			updateBtn();
		});
}

function initializeUI() {
	pushButton.addEventListener('click', function() {
		var industry_name = prompt('Enter industry name')
		pushButton.disabled = true;
		if (isSubscribed) {
			unsubscribeUser(industry_name);
		} else {
			subscribeUser(industry_name);
		}
	});

	swRegistration.pushManager.getSubscription()
		.then(function(subscription) {
			isSubscribed = !(subscription === null);

			if (isSubscribed) {
				console.log('User IS subscribed.');
			} else {
				console.log('User is NOT subscribed.');
			}
			updateBtn();
		});
}

if ('serviceWorker' in navigator && 'PushManager' in window) {
	console.log('Service Worker and Push is supported');

	navigator.serviceWorker.register("/static/sw.js")
		.then(function(swReg) {
			console.log('Service Worker is registered', swReg);

			swRegistration = swReg;
			initializeUI();
		})
		.catch(function(error) {
			console.error('Service Worker Error', error);
		});
} else {
	console.warn('Push meapplicationServerPublicKeyssaging is not supported');
	pushButton.textContent = 'Push Not Supported';
}

$(document).ready(function(){
	$.ajax({
		type:"GET",
		url:'/api/v1/vapid/public/key',
		success:function(response){
			console.log("response",response);
			localStorage.setItem('applicationServerPublicKey',response.public_key);
		}
	})
});
