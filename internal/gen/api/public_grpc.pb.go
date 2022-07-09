// Code generated by protoc-gen-go-grpc. DO NOT EDIT.

package api

import (
	context "context"
	grpc "google.golang.org/grpc"
	codes "google.golang.org/grpc/codes"
	status "google.golang.org/grpc/status"
)

// This is a compile-time assertion to ensure that this generated file
// is compatible with the grpc package it is being compiled against.
// Requires gRPC-Go v1.32.0 or later.
const _ = grpc.SupportPackageIsVersion7

// PublicClient is the client API for Public service.
//
// For semantics around ctx use and closing/ending streaming RPCs, please refer to https://pkg.go.dev/google.golang.org/grpc/?tab=doc#ClientConn.NewStream.
type PublicClient interface {
	Entrypoint(ctx context.Context, in *EntrypointRequest, opts ...grpc.CallOption) (*EntrypointReply, error)
	ListSystems(ctx context.Context, in *ListSystemsRequest, opts ...grpc.CallOption) (*ListSystemsReply, error)
	GetSystem(ctx context.Context, in *GetSystemRequest, opts ...grpc.CallOption) (*System, error)
	ListAgencies(ctx context.Context, in *ListAgenciesRequest, opts ...grpc.CallOption) (*ListAgenciesReply, error)
	GetAgency(ctx context.Context, in *GetAgencyRequest, opts ...grpc.CallOption) (*Agency, error)
	ListStops(ctx context.Context, in *ListStopsRequest, opts ...grpc.CallOption) (*ListStopsReply, error)
	GetStop(ctx context.Context, in *GetStopRequest, opts ...grpc.CallOption) (*Stop, error)
	ListRoutes(ctx context.Context, in *ListRoutesRequest, opts ...grpc.CallOption) (*ListRoutesReply, error)
	GetRoute(ctx context.Context, in *GetRouteRequest, opts ...grpc.CallOption) (*Route, error)
	ListTrips(ctx context.Context, in *ListTripsRequest, opts ...grpc.CallOption) (*ListTripsReply, error)
	GetTrip(ctx context.Context, in *GetTripRequest, opts ...grpc.CallOption) (*Trip, error)
	ListAlerts(ctx context.Context, in *ListAlertsRequest, opts ...grpc.CallOption) (*ListAlertsReply, error)
	GetAlert(ctx context.Context, in *GetAlertRequest, opts ...grpc.CallOption) (*Alert, error)
	ListFeeds(ctx context.Context, in *ListFeedsRequest, opts ...grpc.CallOption) (*ListFeedsReply, error)
	GetFeed(ctx context.Context, in *GetFeedRequest, opts ...grpc.CallOption) (*Feed, error)
	ListFeedUpdates(ctx context.Context, in *ListFeedUpdatesRequest, opts ...grpc.CallOption) (*ListFeedUpdatesReply, error)
	ListTransfers(ctx context.Context, in *ListTransfersRequest, opts ...grpc.CallOption) (*ListTransfersReply, error)
}

type publicClient struct {
	cc grpc.ClientConnInterface
}

func NewPublicClient(cc grpc.ClientConnInterface) PublicClient {
	return &publicClient{cc}
}

func (c *publicClient) Entrypoint(ctx context.Context, in *EntrypointRequest, opts ...grpc.CallOption) (*EntrypointReply, error) {
	out := new(EntrypointReply)
	err := c.cc.Invoke(ctx, "/Public/Entrypoint", in, out, opts...)
	if err != nil {
		return nil, err
	}
	return out, nil
}

func (c *publicClient) ListSystems(ctx context.Context, in *ListSystemsRequest, opts ...grpc.CallOption) (*ListSystemsReply, error) {
	out := new(ListSystemsReply)
	err := c.cc.Invoke(ctx, "/Public/ListSystems", in, out, opts...)
	if err != nil {
		return nil, err
	}
	return out, nil
}

func (c *publicClient) GetSystem(ctx context.Context, in *GetSystemRequest, opts ...grpc.CallOption) (*System, error) {
	out := new(System)
	err := c.cc.Invoke(ctx, "/Public/GetSystem", in, out, opts...)
	if err != nil {
		return nil, err
	}
	return out, nil
}

func (c *publicClient) ListAgencies(ctx context.Context, in *ListAgenciesRequest, opts ...grpc.CallOption) (*ListAgenciesReply, error) {
	out := new(ListAgenciesReply)
	err := c.cc.Invoke(ctx, "/Public/ListAgencies", in, out, opts...)
	if err != nil {
		return nil, err
	}
	return out, nil
}

func (c *publicClient) GetAgency(ctx context.Context, in *GetAgencyRequest, opts ...grpc.CallOption) (*Agency, error) {
	out := new(Agency)
	err := c.cc.Invoke(ctx, "/Public/GetAgency", in, out, opts...)
	if err != nil {
		return nil, err
	}
	return out, nil
}

func (c *publicClient) ListStops(ctx context.Context, in *ListStopsRequest, opts ...grpc.CallOption) (*ListStopsReply, error) {
	out := new(ListStopsReply)
	err := c.cc.Invoke(ctx, "/Public/ListStops", in, out, opts...)
	if err != nil {
		return nil, err
	}
	return out, nil
}

func (c *publicClient) GetStop(ctx context.Context, in *GetStopRequest, opts ...grpc.CallOption) (*Stop, error) {
	out := new(Stop)
	err := c.cc.Invoke(ctx, "/Public/GetStop", in, out, opts...)
	if err != nil {
		return nil, err
	}
	return out, nil
}

func (c *publicClient) ListRoutes(ctx context.Context, in *ListRoutesRequest, opts ...grpc.CallOption) (*ListRoutesReply, error) {
	out := new(ListRoutesReply)
	err := c.cc.Invoke(ctx, "/Public/ListRoutes", in, out, opts...)
	if err != nil {
		return nil, err
	}
	return out, nil
}

func (c *publicClient) GetRoute(ctx context.Context, in *GetRouteRequest, opts ...grpc.CallOption) (*Route, error) {
	out := new(Route)
	err := c.cc.Invoke(ctx, "/Public/GetRoute", in, out, opts...)
	if err != nil {
		return nil, err
	}
	return out, nil
}

func (c *publicClient) ListTrips(ctx context.Context, in *ListTripsRequest, opts ...grpc.CallOption) (*ListTripsReply, error) {
	out := new(ListTripsReply)
	err := c.cc.Invoke(ctx, "/Public/ListTrips", in, out, opts...)
	if err != nil {
		return nil, err
	}
	return out, nil
}

func (c *publicClient) GetTrip(ctx context.Context, in *GetTripRequest, opts ...grpc.CallOption) (*Trip, error) {
	out := new(Trip)
	err := c.cc.Invoke(ctx, "/Public/GetTrip", in, out, opts...)
	if err != nil {
		return nil, err
	}
	return out, nil
}

func (c *publicClient) ListAlerts(ctx context.Context, in *ListAlertsRequest, opts ...grpc.CallOption) (*ListAlertsReply, error) {
	out := new(ListAlertsReply)
	err := c.cc.Invoke(ctx, "/Public/ListAlerts", in, out, opts...)
	if err != nil {
		return nil, err
	}
	return out, nil
}

func (c *publicClient) GetAlert(ctx context.Context, in *GetAlertRequest, opts ...grpc.CallOption) (*Alert, error) {
	out := new(Alert)
	err := c.cc.Invoke(ctx, "/Public/GetAlert", in, out, opts...)
	if err != nil {
		return nil, err
	}
	return out, nil
}

func (c *publicClient) ListFeeds(ctx context.Context, in *ListFeedsRequest, opts ...grpc.CallOption) (*ListFeedsReply, error) {
	out := new(ListFeedsReply)
	err := c.cc.Invoke(ctx, "/Public/ListFeeds", in, out, opts...)
	if err != nil {
		return nil, err
	}
	return out, nil
}

func (c *publicClient) GetFeed(ctx context.Context, in *GetFeedRequest, opts ...grpc.CallOption) (*Feed, error) {
	out := new(Feed)
	err := c.cc.Invoke(ctx, "/Public/GetFeed", in, out, opts...)
	if err != nil {
		return nil, err
	}
	return out, nil
}

func (c *publicClient) ListFeedUpdates(ctx context.Context, in *ListFeedUpdatesRequest, opts ...grpc.CallOption) (*ListFeedUpdatesReply, error) {
	out := new(ListFeedUpdatesReply)
	err := c.cc.Invoke(ctx, "/Public/ListFeedUpdates", in, out, opts...)
	if err != nil {
		return nil, err
	}
	return out, nil
}

func (c *publicClient) ListTransfers(ctx context.Context, in *ListTransfersRequest, opts ...grpc.CallOption) (*ListTransfersReply, error) {
	out := new(ListTransfersReply)
	err := c.cc.Invoke(ctx, "/Public/ListTransfers", in, out, opts...)
	if err != nil {
		return nil, err
	}
	return out, nil
}

// PublicServer is the server API for Public service.
// All implementations should embed UnimplementedPublicServer
// for forward compatibility
type PublicServer interface {
	Entrypoint(context.Context, *EntrypointRequest) (*EntrypointReply, error)
	ListSystems(context.Context, *ListSystemsRequest) (*ListSystemsReply, error)
	GetSystem(context.Context, *GetSystemRequest) (*System, error)
	ListAgencies(context.Context, *ListAgenciesRequest) (*ListAgenciesReply, error)
	GetAgency(context.Context, *GetAgencyRequest) (*Agency, error)
	ListStops(context.Context, *ListStopsRequest) (*ListStopsReply, error)
	GetStop(context.Context, *GetStopRequest) (*Stop, error)
	ListRoutes(context.Context, *ListRoutesRequest) (*ListRoutesReply, error)
	GetRoute(context.Context, *GetRouteRequest) (*Route, error)
	ListTrips(context.Context, *ListTripsRequest) (*ListTripsReply, error)
	GetTrip(context.Context, *GetTripRequest) (*Trip, error)
	ListAlerts(context.Context, *ListAlertsRequest) (*ListAlertsReply, error)
	GetAlert(context.Context, *GetAlertRequest) (*Alert, error)
	ListFeeds(context.Context, *ListFeedsRequest) (*ListFeedsReply, error)
	GetFeed(context.Context, *GetFeedRequest) (*Feed, error)
	ListFeedUpdates(context.Context, *ListFeedUpdatesRequest) (*ListFeedUpdatesReply, error)
	ListTransfers(context.Context, *ListTransfersRequest) (*ListTransfersReply, error)
}

// UnimplementedPublicServer should be embedded to have forward compatible implementations.
type UnimplementedPublicServer struct {
}

func (UnimplementedPublicServer) Entrypoint(context.Context, *EntrypointRequest) (*EntrypointReply, error) {
	return nil, status.Errorf(codes.Unimplemented, "method Entrypoint not implemented")
}
func (UnimplementedPublicServer) ListSystems(context.Context, *ListSystemsRequest) (*ListSystemsReply, error) {
	return nil, status.Errorf(codes.Unimplemented, "method ListSystems not implemented")
}
func (UnimplementedPublicServer) GetSystem(context.Context, *GetSystemRequest) (*System, error) {
	return nil, status.Errorf(codes.Unimplemented, "method GetSystem not implemented")
}
func (UnimplementedPublicServer) ListAgencies(context.Context, *ListAgenciesRequest) (*ListAgenciesReply, error) {
	return nil, status.Errorf(codes.Unimplemented, "method ListAgencies not implemented")
}
func (UnimplementedPublicServer) GetAgency(context.Context, *GetAgencyRequest) (*Agency, error) {
	return nil, status.Errorf(codes.Unimplemented, "method GetAgency not implemented")
}
func (UnimplementedPublicServer) ListStops(context.Context, *ListStopsRequest) (*ListStopsReply, error) {
	return nil, status.Errorf(codes.Unimplemented, "method ListStops not implemented")
}
func (UnimplementedPublicServer) GetStop(context.Context, *GetStopRequest) (*Stop, error) {
	return nil, status.Errorf(codes.Unimplemented, "method GetStop not implemented")
}
func (UnimplementedPublicServer) ListRoutes(context.Context, *ListRoutesRequest) (*ListRoutesReply, error) {
	return nil, status.Errorf(codes.Unimplemented, "method ListRoutes not implemented")
}
func (UnimplementedPublicServer) GetRoute(context.Context, *GetRouteRequest) (*Route, error) {
	return nil, status.Errorf(codes.Unimplemented, "method GetRoute not implemented")
}
func (UnimplementedPublicServer) ListTrips(context.Context, *ListTripsRequest) (*ListTripsReply, error) {
	return nil, status.Errorf(codes.Unimplemented, "method ListTrips not implemented")
}
func (UnimplementedPublicServer) GetTrip(context.Context, *GetTripRequest) (*Trip, error) {
	return nil, status.Errorf(codes.Unimplemented, "method GetTrip not implemented")
}
func (UnimplementedPublicServer) ListAlerts(context.Context, *ListAlertsRequest) (*ListAlertsReply, error) {
	return nil, status.Errorf(codes.Unimplemented, "method ListAlerts not implemented")
}
func (UnimplementedPublicServer) GetAlert(context.Context, *GetAlertRequest) (*Alert, error) {
	return nil, status.Errorf(codes.Unimplemented, "method GetAlert not implemented")
}
func (UnimplementedPublicServer) ListFeeds(context.Context, *ListFeedsRequest) (*ListFeedsReply, error) {
	return nil, status.Errorf(codes.Unimplemented, "method ListFeeds not implemented")
}
func (UnimplementedPublicServer) GetFeed(context.Context, *GetFeedRequest) (*Feed, error) {
	return nil, status.Errorf(codes.Unimplemented, "method GetFeed not implemented")
}
func (UnimplementedPublicServer) ListFeedUpdates(context.Context, *ListFeedUpdatesRequest) (*ListFeedUpdatesReply, error) {
	return nil, status.Errorf(codes.Unimplemented, "method ListFeedUpdates not implemented")
}
func (UnimplementedPublicServer) ListTransfers(context.Context, *ListTransfersRequest) (*ListTransfersReply, error) {
	return nil, status.Errorf(codes.Unimplemented, "method ListTransfers not implemented")
}

// UnsafePublicServer may be embedded to opt out of forward compatibility for this service.
// Use of this interface is not recommended, as added methods to PublicServer will
// result in compilation errors.
type UnsafePublicServer interface {
	mustEmbedUnimplementedPublicServer()
}

func RegisterPublicServer(s grpc.ServiceRegistrar, srv PublicServer) {
	s.RegisterService(&Public_ServiceDesc, srv)
}

func _Public_Entrypoint_Handler(srv interface{}, ctx context.Context, dec func(interface{}) error, interceptor grpc.UnaryServerInterceptor) (interface{}, error) {
	in := new(EntrypointRequest)
	if err := dec(in); err != nil {
		return nil, err
	}
	if interceptor == nil {
		return srv.(PublicServer).Entrypoint(ctx, in)
	}
	info := &grpc.UnaryServerInfo{
		Server:     srv,
		FullMethod: "/Public/Entrypoint",
	}
	handler := func(ctx context.Context, req interface{}) (interface{}, error) {
		return srv.(PublicServer).Entrypoint(ctx, req.(*EntrypointRequest))
	}
	return interceptor(ctx, in, info, handler)
}

func _Public_ListSystems_Handler(srv interface{}, ctx context.Context, dec func(interface{}) error, interceptor grpc.UnaryServerInterceptor) (interface{}, error) {
	in := new(ListSystemsRequest)
	if err := dec(in); err != nil {
		return nil, err
	}
	if interceptor == nil {
		return srv.(PublicServer).ListSystems(ctx, in)
	}
	info := &grpc.UnaryServerInfo{
		Server:     srv,
		FullMethod: "/Public/ListSystems",
	}
	handler := func(ctx context.Context, req interface{}) (interface{}, error) {
		return srv.(PublicServer).ListSystems(ctx, req.(*ListSystemsRequest))
	}
	return interceptor(ctx, in, info, handler)
}

func _Public_GetSystem_Handler(srv interface{}, ctx context.Context, dec func(interface{}) error, interceptor grpc.UnaryServerInterceptor) (interface{}, error) {
	in := new(GetSystemRequest)
	if err := dec(in); err != nil {
		return nil, err
	}
	if interceptor == nil {
		return srv.(PublicServer).GetSystem(ctx, in)
	}
	info := &grpc.UnaryServerInfo{
		Server:     srv,
		FullMethod: "/Public/GetSystem",
	}
	handler := func(ctx context.Context, req interface{}) (interface{}, error) {
		return srv.(PublicServer).GetSystem(ctx, req.(*GetSystemRequest))
	}
	return interceptor(ctx, in, info, handler)
}

func _Public_ListAgencies_Handler(srv interface{}, ctx context.Context, dec func(interface{}) error, interceptor grpc.UnaryServerInterceptor) (interface{}, error) {
	in := new(ListAgenciesRequest)
	if err := dec(in); err != nil {
		return nil, err
	}
	if interceptor == nil {
		return srv.(PublicServer).ListAgencies(ctx, in)
	}
	info := &grpc.UnaryServerInfo{
		Server:     srv,
		FullMethod: "/Public/ListAgencies",
	}
	handler := func(ctx context.Context, req interface{}) (interface{}, error) {
		return srv.(PublicServer).ListAgencies(ctx, req.(*ListAgenciesRequest))
	}
	return interceptor(ctx, in, info, handler)
}

func _Public_GetAgency_Handler(srv interface{}, ctx context.Context, dec func(interface{}) error, interceptor grpc.UnaryServerInterceptor) (interface{}, error) {
	in := new(GetAgencyRequest)
	if err := dec(in); err != nil {
		return nil, err
	}
	if interceptor == nil {
		return srv.(PublicServer).GetAgency(ctx, in)
	}
	info := &grpc.UnaryServerInfo{
		Server:     srv,
		FullMethod: "/Public/GetAgency",
	}
	handler := func(ctx context.Context, req interface{}) (interface{}, error) {
		return srv.(PublicServer).GetAgency(ctx, req.(*GetAgencyRequest))
	}
	return interceptor(ctx, in, info, handler)
}

func _Public_ListStops_Handler(srv interface{}, ctx context.Context, dec func(interface{}) error, interceptor grpc.UnaryServerInterceptor) (interface{}, error) {
	in := new(ListStopsRequest)
	if err := dec(in); err != nil {
		return nil, err
	}
	if interceptor == nil {
		return srv.(PublicServer).ListStops(ctx, in)
	}
	info := &grpc.UnaryServerInfo{
		Server:     srv,
		FullMethod: "/Public/ListStops",
	}
	handler := func(ctx context.Context, req interface{}) (interface{}, error) {
		return srv.(PublicServer).ListStops(ctx, req.(*ListStopsRequest))
	}
	return interceptor(ctx, in, info, handler)
}

func _Public_GetStop_Handler(srv interface{}, ctx context.Context, dec func(interface{}) error, interceptor grpc.UnaryServerInterceptor) (interface{}, error) {
	in := new(GetStopRequest)
	if err := dec(in); err != nil {
		return nil, err
	}
	if interceptor == nil {
		return srv.(PublicServer).GetStop(ctx, in)
	}
	info := &grpc.UnaryServerInfo{
		Server:     srv,
		FullMethod: "/Public/GetStop",
	}
	handler := func(ctx context.Context, req interface{}) (interface{}, error) {
		return srv.(PublicServer).GetStop(ctx, req.(*GetStopRequest))
	}
	return interceptor(ctx, in, info, handler)
}

func _Public_ListRoutes_Handler(srv interface{}, ctx context.Context, dec func(interface{}) error, interceptor grpc.UnaryServerInterceptor) (interface{}, error) {
	in := new(ListRoutesRequest)
	if err := dec(in); err != nil {
		return nil, err
	}
	if interceptor == nil {
		return srv.(PublicServer).ListRoutes(ctx, in)
	}
	info := &grpc.UnaryServerInfo{
		Server:     srv,
		FullMethod: "/Public/ListRoutes",
	}
	handler := func(ctx context.Context, req interface{}) (interface{}, error) {
		return srv.(PublicServer).ListRoutes(ctx, req.(*ListRoutesRequest))
	}
	return interceptor(ctx, in, info, handler)
}

func _Public_GetRoute_Handler(srv interface{}, ctx context.Context, dec func(interface{}) error, interceptor grpc.UnaryServerInterceptor) (interface{}, error) {
	in := new(GetRouteRequest)
	if err := dec(in); err != nil {
		return nil, err
	}
	if interceptor == nil {
		return srv.(PublicServer).GetRoute(ctx, in)
	}
	info := &grpc.UnaryServerInfo{
		Server:     srv,
		FullMethod: "/Public/GetRoute",
	}
	handler := func(ctx context.Context, req interface{}) (interface{}, error) {
		return srv.(PublicServer).GetRoute(ctx, req.(*GetRouteRequest))
	}
	return interceptor(ctx, in, info, handler)
}

func _Public_ListTrips_Handler(srv interface{}, ctx context.Context, dec func(interface{}) error, interceptor grpc.UnaryServerInterceptor) (interface{}, error) {
	in := new(ListTripsRequest)
	if err := dec(in); err != nil {
		return nil, err
	}
	if interceptor == nil {
		return srv.(PublicServer).ListTrips(ctx, in)
	}
	info := &grpc.UnaryServerInfo{
		Server:     srv,
		FullMethod: "/Public/ListTrips",
	}
	handler := func(ctx context.Context, req interface{}) (interface{}, error) {
		return srv.(PublicServer).ListTrips(ctx, req.(*ListTripsRequest))
	}
	return interceptor(ctx, in, info, handler)
}

func _Public_GetTrip_Handler(srv interface{}, ctx context.Context, dec func(interface{}) error, interceptor grpc.UnaryServerInterceptor) (interface{}, error) {
	in := new(GetTripRequest)
	if err := dec(in); err != nil {
		return nil, err
	}
	if interceptor == nil {
		return srv.(PublicServer).GetTrip(ctx, in)
	}
	info := &grpc.UnaryServerInfo{
		Server:     srv,
		FullMethod: "/Public/GetTrip",
	}
	handler := func(ctx context.Context, req interface{}) (interface{}, error) {
		return srv.(PublicServer).GetTrip(ctx, req.(*GetTripRequest))
	}
	return interceptor(ctx, in, info, handler)
}

func _Public_ListAlerts_Handler(srv interface{}, ctx context.Context, dec func(interface{}) error, interceptor grpc.UnaryServerInterceptor) (interface{}, error) {
	in := new(ListAlertsRequest)
	if err := dec(in); err != nil {
		return nil, err
	}
	if interceptor == nil {
		return srv.(PublicServer).ListAlerts(ctx, in)
	}
	info := &grpc.UnaryServerInfo{
		Server:     srv,
		FullMethod: "/Public/ListAlerts",
	}
	handler := func(ctx context.Context, req interface{}) (interface{}, error) {
		return srv.(PublicServer).ListAlerts(ctx, req.(*ListAlertsRequest))
	}
	return interceptor(ctx, in, info, handler)
}

func _Public_GetAlert_Handler(srv interface{}, ctx context.Context, dec func(interface{}) error, interceptor grpc.UnaryServerInterceptor) (interface{}, error) {
	in := new(GetAlertRequest)
	if err := dec(in); err != nil {
		return nil, err
	}
	if interceptor == nil {
		return srv.(PublicServer).GetAlert(ctx, in)
	}
	info := &grpc.UnaryServerInfo{
		Server:     srv,
		FullMethod: "/Public/GetAlert",
	}
	handler := func(ctx context.Context, req interface{}) (interface{}, error) {
		return srv.(PublicServer).GetAlert(ctx, req.(*GetAlertRequest))
	}
	return interceptor(ctx, in, info, handler)
}

func _Public_ListFeeds_Handler(srv interface{}, ctx context.Context, dec func(interface{}) error, interceptor grpc.UnaryServerInterceptor) (interface{}, error) {
	in := new(ListFeedsRequest)
	if err := dec(in); err != nil {
		return nil, err
	}
	if interceptor == nil {
		return srv.(PublicServer).ListFeeds(ctx, in)
	}
	info := &grpc.UnaryServerInfo{
		Server:     srv,
		FullMethod: "/Public/ListFeeds",
	}
	handler := func(ctx context.Context, req interface{}) (interface{}, error) {
		return srv.(PublicServer).ListFeeds(ctx, req.(*ListFeedsRequest))
	}
	return interceptor(ctx, in, info, handler)
}

func _Public_GetFeed_Handler(srv interface{}, ctx context.Context, dec func(interface{}) error, interceptor grpc.UnaryServerInterceptor) (interface{}, error) {
	in := new(GetFeedRequest)
	if err := dec(in); err != nil {
		return nil, err
	}
	if interceptor == nil {
		return srv.(PublicServer).GetFeed(ctx, in)
	}
	info := &grpc.UnaryServerInfo{
		Server:     srv,
		FullMethod: "/Public/GetFeed",
	}
	handler := func(ctx context.Context, req interface{}) (interface{}, error) {
		return srv.(PublicServer).GetFeed(ctx, req.(*GetFeedRequest))
	}
	return interceptor(ctx, in, info, handler)
}

func _Public_ListFeedUpdates_Handler(srv interface{}, ctx context.Context, dec func(interface{}) error, interceptor grpc.UnaryServerInterceptor) (interface{}, error) {
	in := new(ListFeedUpdatesRequest)
	if err := dec(in); err != nil {
		return nil, err
	}
	if interceptor == nil {
		return srv.(PublicServer).ListFeedUpdates(ctx, in)
	}
	info := &grpc.UnaryServerInfo{
		Server:     srv,
		FullMethod: "/Public/ListFeedUpdates",
	}
	handler := func(ctx context.Context, req interface{}) (interface{}, error) {
		return srv.(PublicServer).ListFeedUpdates(ctx, req.(*ListFeedUpdatesRequest))
	}
	return interceptor(ctx, in, info, handler)
}

func _Public_ListTransfers_Handler(srv interface{}, ctx context.Context, dec func(interface{}) error, interceptor grpc.UnaryServerInterceptor) (interface{}, error) {
	in := new(ListTransfersRequest)
	if err := dec(in); err != nil {
		return nil, err
	}
	if interceptor == nil {
		return srv.(PublicServer).ListTransfers(ctx, in)
	}
	info := &grpc.UnaryServerInfo{
		Server:     srv,
		FullMethod: "/Public/ListTransfers",
	}
	handler := func(ctx context.Context, req interface{}) (interface{}, error) {
		return srv.(PublicServer).ListTransfers(ctx, req.(*ListTransfersRequest))
	}
	return interceptor(ctx, in, info, handler)
}

// Public_ServiceDesc is the grpc.ServiceDesc for Public service.
// It's only intended for direct use with grpc.RegisterService,
// and not to be introspected or modified (even as a copy)
var Public_ServiceDesc = grpc.ServiceDesc{
	ServiceName: "Public",
	HandlerType: (*PublicServer)(nil),
	Methods: []grpc.MethodDesc{
		{
			MethodName: "Entrypoint",
			Handler:    _Public_Entrypoint_Handler,
		},
		{
			MethodName: "ListSystems",
			Handler:    _Public_ListSystems_Handler,
		},
		{
			MethodName: "GetSystem",
			Handler:    _Public_GetSystem_Handler,
		},
		{
			MethodName: "ListAgencies",
			Handler:    _Public_ListAgencies_Handler,
		},
		{
			MethodName: "GetAgency",
			Handler:    _Public_GetAgency_Handler,
		},
		{
			MethodName: "ListStops",
			Handler:    _Public_ListStops_Handler,
		},
		{
			MethodName: "GetStop",
			Handler:    _Public_GetStop_Handler,
		},
		{
			MethodName: "ListRoutes",
			Handler:    _Public_ListRoutes_Handler,
		},
		{
			MethodName: "GetRoute",
			Handler:    _Public_GetRoute_Handler,
		},
		{
			MethodName: "ListTrips",
			Handler:    _Public_ListTrips_Handler,
		},
		{
			MethodName: "GetTrip",
			Handler:    _Public_GetTrip_Handler,
		},
		{
			MethodName: "ListAlerts",
			Handler:    _Public_ListAlerts_Handler,
		},
		{
			MethodName: "GetAlert",
			Handler:    _Public_GetAlert_Handler,
		},
		{
			MethodName: "ListFeeds",
			Handler:    _Public_ListFeeds_Handler,
		},
		{
			MethodName: "GetFeed",
			Handler:    _Public_GetFeed_Handler,
		},
		{
			MethodName: "ListFeedUpdates",
			Handler:    _Public_ListFeedUpdates_Handler,
		},
		{
			MethodName: "ListTransfers",
			Handler:    _Public_ListTransfers_Handler,
		},
	},
	Streams:  []grpc.StreamDesc{},
	Metadata: "api/public.proto",
}